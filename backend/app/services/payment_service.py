"""Razorpay yearly premium membership and reconciliation."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import urllib.error
import urllib.request
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.core.premium import extend_premium_year, premium_is_active, sync_premium_flag
from app.models import Payment, PaymentAttempt, PaymentWebhookEvent, PremiumGrant, User


def _as_utc(value: datetime) -> datetime:
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


def recompute_premium(db: Session, user: User, *, now: datetime | None = None) -> User:
    """Rebuild the user's entitlement from non-revoked captured-payment grants."""
    now = now or datetime.now(UTC)
    grants = db.scalars(
        select(PremiumGrant)
        .where(PremiumGrant.user_id == user.id, PremiumGrant.revoked_at.is_(None))
        .order_by(PremiumGrant.granted_at, PremiumGrant.id)
    ).all()
    expires_at: datetime | None = None
    for grant in grants:
        granted_at = _as_utc(grant.granted_at)
        base = granted_at if expires_at is None or granted_at > expires_at else expires_at
        expires_at = base + timedelta(days=grant.duration_days)
    user.premium_activated_at = _as_utc(grants[0].granted_at) if grants else None
    user.premium_until = expires_at
    user.is_premium = bool(expires_at and expires_at >= now)
    return user


def _razorpay_auth_header() -> str:
    raw = f"{settings.razorpay_key_id}:{settings.razorpay_key_secret}".encode()
    return "Basic " + base64.b64encode(raw).decode()


def _razorpay_request(
    method: str, path: str, payload: dict[str, Any] | None = None
) -> dict[str, Any]:
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        f"https://api.razorpay.com/v1{path}",
        data=data,
        method=method,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": _razorpay_auth_header(),
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Razorpay rejected the payment request",
        ) from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not reach Razorpay. Please try again.",
        ) from exc


def create_razorpay_order(db: Session, user: User, *, currency: str = "INR") -> dict:
    sync_premium_flag(user)
    if not settings.razorpay_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payments are not configured. Set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET.",
        )

    currency = currency.upper().strip()
    if currency != "INR":
        raise HTTPException(
            status_code=400,
            detail="Razorpay checkout is INR only. Use international checkout outside India.",
        )

    amount = settings.premium_amount_paise
    payload = {
        "amount": amount,
        "currency": "INR",
        "receipt": f"om_user_{user.id}_{int(datetime.now(UTC).timestamp())}",
        "notes": {
            "user_id": str(user.id),
            "email": user.email,
            "plan": "yearly",
        },
    }
    order = _razorpay_request("POST", "/orders", payload)

    payment = Payment(
        user_id=user.id,
        provider="razorpay",
        amount_paise=amount,
        currency="INR",
        status="created",
        razorpay_order_id=order["id"],
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    return {
        "order_id": order["id"],
        "amount_paise": amount,
        "currency": "INR",
        "key_id": settings.razorpay_key_id,
        "name": "OpportunityMap Premium",
        "description": (
            f"Yearly membership — profile, recommendations & notifications "
            f"(₹{settings.premium_price_inr}/year; +365 days from payment)"
        ),
        "prefill_email": user.email,
        "payment_id": payment.id,
    }


def _payment_for_update(db: Session, order_id: str) -> Payment:
    payment = db.scalar(
        select(Payment)
        .where(Payment.razorpay_order_id == order_id)
        .with_for_update()
    )
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment order not found")
    return payment


def _provider_datetime(entity: dict[str, Any]) -> datetime:
    created_at = entity.get("created_at")
    if isinstance(created_at, int):
        return datetime.fromtimestamp(created_at, tz=UTC)
    return datetime.now(UTC)


def _apply_payment_entity(
    db: Session,
    entity: dict[str, Any],
    *,
    expected_user_id: int | None = None,
) -> tuple[Payment, User]:
    order_id = entity.get("order_id")
    payment_id = entity.get("id")
    if not isinstance(order_id, str) or not isinstance(payment_id, str):
        raise HTTPException(status_code=400, detail="Payment event is missing identifiers")

    payment = _payment_for_update(db, order_id)
    if expected_user_id is not None and payment.user_id != expected_user_id:
        raise HTTPException(status_code=404, detail="Payment order not found")
    if entity.get("amount") != payment.amount_paise or entity.get("currency") != payment.currency:
        raise HTTPException(status_code=400, detail="Payment amount or currency does not match")

    user = db.scalar(select(User).where(User.id == payment.user_id).with_for_update())
    if user is None:
        raise HTTPException(status_code=404, detail="Payment user not found")

    attempt = db.scalar(
        select(PaymentAttempt).where(PaymentAttempt.razorpay_payment_id == payment_id)
    )
    if attempt is not None and attempt.payment_id != payment.id:
        raise HTTPException(status_code=400, detail="Payment identifier belongs to another order")
    if attempt is None:
        attempt = PaymentAttempt(
            payment_id=payment.id,
            razorpay_payment_id=payment_id,
            status=str(entity.get("status") or "created"),
            amount_paise=int(entity["amount"]),
            currency=str(entity["currency"]),
        )
        db.add(attempt)
        db.flush()

    provider_status = str(entity.get("status") or attempt.status)
    attempt.status = provider_status
    attempt.amount_refunded_paise = int(entity.get("amount_refunded") or 0)
    attempt.error_code = entity.get("error_code")
    attempt.error_description = entity.get("error_description")

    if provider_status == "captured":
        captured_at = _provider_datetime(entity)
        attempt.captured_at = attempt.captured_at or captured_at
        payment.status = "paid"
        payment.razorpay_payment_id = payment_id
        payment.paid_at = payment.paid_at or captured_at
        grant = db.scalar(
            select(PremiumGrant).where(PremiumGrant.payment_attempt_id == attempt.id)
        )
        if grant is None:
            db.add(
                PremiumGrant(
                    user_id=user.id,
                    payment_attempt_id=attempt.id,
                    duration_days=365,
                    granted_at=captured_at,
                )
            )
            db.flush()
            # A fresh purchase opts the user into renewal reminders by default.
            user.auto_renew = True
        recompute_premium(db, user)
    elif provider_status == "failed":
        if payment.status != "paid":
            payment.status = "failed"

    fully_refunded = (
        attempt.amount_refunded_paise >= attempt.amount_paise
        or provider_status == "refunded"
    )
    if fully_refunded:
        payment.status = "refunded"
        attempt.status = "refunded"
        grant = db.scalar(
            select(PremiumGrant).where(PremiumGrant.payment_attempt_id == attempt.id)
        )
        if grant is not None and grant.revoked_at is None:
            grant.revoked_at = datetime.now(UTC)
            grant.revocation_reason = "Full Razorpay refund"
            recompute_premium(db, user)
    return payment, user


def verify_razorpay_payment(
    db: Session,
    user: User,
    *,
    razorpay_order_id: str,
    razorpay_payment_id: str,
    razorpay_signature: str,
) -> User:
    if not settings.razorpay_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payments are not configured",
        )

    expected = hmac.new(
        settings.razorpay_key_secret.encode(),
        f"{razorpay_order_id}|{razorpay_payment_id}".encode(),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected, razorpay_signature):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payment signature",
        )

    entity = _razorpay_request("GET", f"/payments/{razorpay_payment_id}")
    if entity.get("order_id") != razorpay_order_id:
        raise HTTPException(status_code=400, detail="Payment does not match this order")
    if entity.get("status") != "captured":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Payment is still processing. Your access will update automatically.",
        )
    payment, verified_user = _apply_payment_entity(
        db, entity, expected_user_id=user.id
    )
    payment.razorpay_signature = razorpay_signature
    db.commit()
    db.refresh(verified_user)
    return verified_user


def reconcile_order(db: Session, user: User, order_id: str) -> dict[str, Any]:
    payment = db.scalar(
        select(Payment).where(
            Payment.user_id == user.id,
            Payment.razorpay_order_id == order_id,
        )
    )
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment order not found")

    if settings.razorpay_enabled and payment.status not in {"paid", "refunded"}:
        result = _razorpay_request("GET", f"/orders/{order_id}/payments")
        entities = result.get("items", [])
        for entity in entities:
            if entity.get("status") in {"captured", "failed", "refunded"}:
                payment, user = _apply_payment_entity(
                    db, entity, expected_user_id=user.id
                )
        db.commit()
        db.refresh(user)
    else:
        sync_premium_flag(user)

    return {
        "order_id": order_id,
        "status": payment.status,
        "is_premium": premium_is_active(user),
        "premium_until": user.premium_until,
    }


def verify_webhook_signature(raw_body: bytes, signature: str) -> bool:
    if not settings.razorpay_webhook_secret:
        return False
    expected = hmac.new(
        settings.razorpay_webhook_secret.encode(), raw_body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def process_razorpay_webhook(
    db: Session,
    *,
    raw_body: bytes,
    signature: str,
    event_id: str | None,
) -> None:
    if not settings.razorpay_webhook_secret:
        raise HTTPException(status_code=503, detail="Payment webhooks are not configured")
    if not verify_webhook_signature(raw_body, signature):
        raise HTTPException(status_code=400, detail="Invalid webhook signature")
    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid webhook payload") from exc

    payload_hash = hashlib.sha256(raw_body).hexdigest()
    provider_event_id = event_id or payload_hash
    existing = db.scalar(
        select(PaymentWebhookEvent).where(
            PaymentWebhookEvent.provider_event_id == provider_event_id
        )
    )
    if existing is not None:
        return

    event_type = str(payload.get("event") or "unknown")
    event = PaymentWebhookEvent(
        provider_event_id=provider_event_id,
        event_type=event_type,
        payload_hash=payload_hash,
        payload=payload,
    )
    db.add(event)
    db.flush()

    entity = payload.get("payload", {}).get("payment", {}).get("entity")
    refund = payload.get("payload", {}).get("refund", {}).get("entity")
    if entity is None and isinstance(refund, dict) and refund.get("payment_id"):
        entity = _razorpay_request("GET", f"/payments/{refund['payment_id']}")
    if event_type in {"payment.captured", "payment.failed", "payment.refunded", "refund.processed"}:
        if not isinstance(entity, dict):
            raise HTTPException(status_code=400, detail="Webhook payment entity is missing")
        _apply_payment_entity(db, entity)

    event.processed_at = datetime.now(UTC)
    db.commit()


def dev_unlock(db: Session, user: User) -> User:
    """Explicit local/testing-only unlock."""
    if not settings.dev_unlock_available:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Development premium unlock is disabled",
        )

    sync_premium_flag(user)
    if premium_is_active(user):
        return user

    payment = Payment(
        user_id=user.id,
        provider="dev",
        amount_paise=settings.premium_amount_paise,
        currency="INR",
        status="paid",
        paid_at=datetime.now(UTC),
    )
    db.add(payment)
    extend_premium_year(user)
    db.commit()
    db.refresh(user)
    return user
