"""Polar international yearly subscription checkout for non-India buyers."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import urllib.error
import urllib.request
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Payment, PaymentAttempt, PaymentWebhookEvent, PremiumGrant, User
from app.services.payment_service import recompute_premium


def _polar_request(
    method: str, path: str, payload: dict[str, Any] | None = None
) -> dict[str, Any]:
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        f"{settings.polar_api_base.rstrip('/')}{path}",
        data=data,
        method=method,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.polar_access_token}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Polar rejected the checkout request",
        ) from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not reach Polar. Please try again.",
        ) from exc


def create_checkout(db: Session, user: User) -> dict[str, str]:
    """Start Polar checkout for the configured yearly subscription product."""
    if not settings.polar_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="International checkout is not configured yet.",
        )

    success_url = f"{settings.frontend_url.rstrip('/')}/pricing?polar=success"
    payload = {
        "products": [settings.polar_product_id],
        "customer_email": user.email,
        "external_customer_id": str(user.id),
        "success_url": success_url,
        "metadata": {
            "user_id": str(user.id),
            "email": user.email,
            "plan": "yearly_subscription",
        },
    }
    checkout = _polar_request("POST", "/checkouts/", payload)
    url = checkout.get("url")
    if not isinstance(url, str) or not url:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Polar checkout URL missing",
        )

    checkout_id = str(checkout.get("id") or "")
    payment = Payment(
        user_id=user.id,
        provider="polar",
        amount_paise=settings.premium_amount_usd_cents,
        currency="USD",
        status="created",
        razorpay_order_id=f"polar_checkout_{checkout_id}" if checkout_id else None,
    )
    db.add(payment)
    db.commit()

    return {"checkout_url": url}


def _secret_bytes(secret: str) -> bytes:
    value = secret.strip()
    if value.startswith("whsec_"):
        value = value[len("whsec_") :]
    try:
        return base64.b64decode(value)
    except Exception:
        return secret.encode()


def verify_webhook_signature(
    *,
    raw_body: bytes,
    webhook_id: str,
    webhook_timestamp: str,
    webhook_signature: str,
) -> bool:
    if not settings.polar_webhook_secret:
        return False
    signed = f"{webhook_id}.{webhook_timestamp}.{raw_body.decode('utf-8')}".encode()
    digest = hmac.new(
        _secret_bytes(settings.polar_webhook_secret), signed, hashlib.sha256
    ).digest()
    expected = base64.b64encode(digest).decode()
    for part in webhook_signature.split(" "):
        if "," not in part:
            continue
        version, signature = part.split(",", 1)
        if version == "v1" and hmac.compare_digest(expected, signature):
            return True
    return False


def _user_from_payload(db: Session, entity: dict[str, Any]) -> User | None:
    metadata = entity.get("metadata") or {}
    if isinstance(metadata, dict):
        raw_user_id = metadata.get("user_id")
        if isinstance(raw_user_id, str) and raw_user_id.isdigit():
            user = db.scalar(select(User).where(User.id == int(raw_user_id)))
            if user is not None:
                return user

    customer = entity.get("customer") or {}
    external_id = entity.get("external_customer_id")
    if external_id is None and isinstance(customer, dict):
        external_id = customer.get("external_id")
    if isinstance(external_id, str) and external_id.isdigit():
        user = db.scalar(select(User).where(User.id == int(external_id)))
        if user is not None:
            return user

    email = None
    if isinstance(customer, dict):
        email = customer.get("email")
    if isinstance(email, str) and email.strip():
        return db.scalar(select(User).where(User.email == email.strip().lower()))
    return None


def _apply_paid_order(db: Session, order: dict[str, Any]) -> None:
    """Grant +365 days for subscription create and each yearly renewal cycle."""
    order_id = str(order.get("id") or "")
    if not order_id:
        raise HTTPException(status_code=400, detail="Polar order id missing")

    billing_reason = str(order.get("billing_reason") or "")
    if billing_reason and billing_reason not in {
        "purchase",
        "subscription_create",
        "subscription_cycle",
        "subscription_update",
    }:
        return

    user = _user_from_payload(db, order)
    if user is None:
        raise HTTPException(status_code=404, detail="Polar payment user not found")

    provider_payment_id = f"polar_order_{order_id}"
    attempt = db.scalar(
        select(PaymentAttempt).where(
            PaymentAttempt.razorpay_payment_id == provider_payment_id
        )
    )
    if attempt is not None:
        grant = db.scalar(
            select(PremiumGrant).where(PremiumGrant.payment_attempt_id == attempt.id)
        )
        if grant is not None:
            return

    payment = db.scalar(
        select(Payment)
        .where(Payment.user_id == user.id, Payment.provider == "polar")
        .order_by(Payment.id.desc())
        .with_for_update()
    )
    if payment is None or payment.status == "paid":
        payment = Payment(
            user_id=user.id,
            provider="polar",
            amount_paise=settings.premium_amount_usd_cents,
            currency="USD",
            status="created",
            razorpay_order_id=f"polar_order_{order_id}",
        )
        db.add(payment)
        db.flush()

    paid_at = datetime.now(UTC)
    payment.status = "paid"
    payment.paid_at = payment.paid_at or paid_at
    payment.razorpay_payment_id = provider_payment_id
    payment.currency = "USD"
    payment.amount_paise = settings.premium_amount_usd_cents
    user.auto_renew = True

    if attempt is None:
        attempt = PaymentAttempt(
            payment_id=payment.id,
            razorpay_payment_id=provider_payment_id,
            status="captured",
            amount_paise=settings.premium_amount_usd_cents,
            currency="USD",
            captured_at=paid_at,
        )
        db.add(attempt)
        db.flush()
    else:
        attempt.status = "captured"
        attempt.captured_at = attempt.captured_at or paid_at

    grant = db.scalar(
        select(PremiumGrant).where(PremiumGrant.payment_attempt_id == attempt.id)
    )
    if grant is None:
        db.add(
            PremiumGrant(
                user_id=user.id,
                payment_attempt_id=attempt.id,
                duration_days=365,
                granted_at=paid_at,
            )
        )
        db.flush()
    recompute_premium(db, user)


def _handle_subscription_canceled(db: Session, subscription: dict[str, Any]) -> None:
    """Customer canceled — keep current year, stop treating as auto-renewing."""
    user = _user_from_payload(db, subscription)
    if user is None:
        return
    user.auto_renew = False


def _handle_subscription_revoked(db: Session, subscription: dict[str, Any]) -> None:
    """Subscription fully ended — revoke Polar-funded grants and recompute."""
    user = _user_from_payload(db, subscription)
    if user is None:
        return
    user.auto_renew = False
    now = datetime.now(UTC)
    polar_payments = db.scalars(
        select(Payment).where(Payment.user_id == user.id, Payment.provider == "polar")
    ).all()
    payment_ids = [payment.id for payment in polar_payments]
    if not payment_ids:
        recompute_premium(db, user, now=now)
        return
    attempts = db.scalars(
        select(PaymentAttempt).where(PaymentAttempt.payment_id.in_(payment_ids))
    ).all()
    attempt_ids = [attempt.id for attempt in attempts]
    if attempt_ids:
        grants = db.scalars(
            select(PremiumGrant).where(
                PremiumGrant.payment_attempt_id.in_(attempt_ids),
                PremiumGrant.revoked_at.is_(None),
            )
        ).all()
        for grant in grants:
            grant.revoked_at = now
            grant.revocation_reason = "Polar subscription revoked"
    recompute_premium(db, user, now=now)


def process_webhook(
    db: Session,
    *,
    raw_body: bytes,
    webhook_id: str,
    webhook_timestamp: str,
    webhook_signature: str,
) -> None:
    if not settings.polar_webhook_secret:
        raise HTTPException(status_code=503, detail="Polar webhooks are not configured")
    if not verify_webhook_signature(
        raw_body=raw_body,
        webhook_id=webhook_id,
        webhook_timestamp=webhook_timestamp,
        webhook_signature=webhook_signature,
    ):
        raise HTTPException(status_code=400, detail="Invalid Polar webhook signature")

    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid webhook payload") from exc

    payload_hash = hashlib.sha256(raw_body).hexdigest()
    provider_event_id = webhook_id or payload_hash
    existing = db.scalar(
        select(PaymentWebhookEvent).where(
            PaymentWebhookEvent.provider_event_id == provider_event_id
        )
    )
    if existing is not None:
        return

    event_type = str(payload.get("type") or "unknown")
    event = PaymentWebhookEvent(
        provider_event_id=provider_event_id,
        event_type=f"polar:{event_type}",
        payload_hash=payload_hash,
        payload=payload,
    )
    db.add(event)
    db.flush()

    data = payload.get("data")
    if event_type == "order.paid":
        if not isinstance(data, dict):
            raise HTTPException(status_code=400, detail="Polar order payload missing")
        _apply_paid_order(db, data)
    elif event_type == "subscription.canceled":
        if isinstance(data, dict):
            _handle_subscription_canceled(db, data)
    elif event_type == "subscription.uncanceled":
        if isinstance(data, dict):
            user = _user_from_payload(db, data)
            if user is not None:
                user.auto_renew = True
    elif event_type == "subscription.revoked":
        if isinstance(data, dict):
            _handle_subscription_revoked(db, data)

    event.processed_at = datetime.now(UTC)
    db.commit()
