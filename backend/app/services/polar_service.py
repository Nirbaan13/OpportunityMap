"""Polar international yearly subscription checkout for non-India buyers."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.core.premium import premium_is_active, sync_premium_flag
from app.models import Payment, PaymentAttempt, PaymentWebhookEvent, PremiumGrant, User
from app.services.payment_service import recompute_premium

logger = logging.getLogger(__name__)

# Cloudflare Browser Integrity Check (error 1010) blocks Python's default
# "Python-urllib/x.y" User-Agent. Use an honest app identity — do not spoof a
# browser UA (TLS fingerprint mismatch can also trigger 1010).
_POLAR_USER_AGENT = "OpportunityMap/1.0 (+https://opportunitymap.info; polar-checkout)"

_UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)

_CF_BROWSER_SIGNATURE_RE = re.compile(
    r"browser['\u2019]?s?\s+signature|error code:\s*1010|cf-error-details|attention required",
    re.IGNORECASE,
)


def _is_cloudflare_block(text: str, http_status: int) -> bool:
    if _CF_BROWSER_SIGNATURE_RE.search(text):
        return True
    return (
        http_status == 403
        and "cloudflare" in text.lower()
        and "<html" in text.lower()
    )


def _format_polar_error_body(raw: bytes, http_status: int) -> str:
    """Turn Polar's JSON/text error body into a short, user-visible message."""
    text = raw.decode("utf-8", errors="replace").strip()
    if not text:
        return f"Polar rejected the checkout request (HTTP {http_status})"

    if _is_cloudflare_block(text, http_status):
        return (
            "Polar checkout is temporarily blocked by network protection "
            f"(HTTP {http_status}). Please try again in a moment. "
            "If this keeps happening, contact support."
        )

    try:
        body = json.loads(text)
    except json.JSONDecodeError:
        # Avoid dumping Cloudflare/HTML challenge pages into the UI.
        if "<html" in text.lower() or "<!doctype" in text.lower():
            return (
                f"Polar rejected the checkout request "
                f"(HTTP {http_status}, non-JSON response)."
            )
        return f"Polar rejected the checkout request: {text[:300]}"

    if isinstance(body, dict):
        detail = body.get("detail")
        if isinstance(detail, str) and detail.strip():
            if _is_cloudflare_block(detail, http_status):
                return (
                    "Polar checkout is temporarily blocked by network protection. "
                    "Please try again in a moment."
                )
            return f"Polar rejected the checkout request: {detail.strip()[:400]}"
        if isinstance(detail, list):
            parts: list[str] = []
            for item in detail[:5]:
                if isinstance(item, dict):
                    loc = item.get("loc") or item.get("location")
                    msg = item.get("msg") or item.get("message") or item
                    if isinstance(loc, list) and loc:
                        parts.append(f"{'.'.join(str(x) for x in loc)}: {msg}")
                    else:
                        parts.append(str(msg))
                else:
                    parts.append(str(item))
            if parts:
                return "Polar rejected the checkout request: " + "; ".join(parts)[:400]
        error = body.get("error") or body.get("message")
        if isinstance(error, str) and error.strip():
            return f"Polar rejected the checkout request: {error.strip()[:400]}"

    return f"Polar rejected the checkout request: {text[:300]}"


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
            "User-Agent": _POLAR_USER_AGENT,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        raw = exc.read() if hasattr(exc, "read") else b""
        detail = _format_polar_error_body(raw, exc.code)
        logger.error(
            "Polar %s %s failed (%s): %s",
            method,
            path,
            exc.code,
            raw.decode("utf-8", errors="replace")[:1000],
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=detail,
        ) from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not reach Polar. Please try again.",
        ) from exc


def _require_polar_product_id() -> str:
    product_id = settings.polar_product_id.strip()
    if not product_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="International checkout is not configured yet.",
        )
    if not _UUID_RE.match(product_id):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "POLAR_PRODUCT_ID must be the product UUID from Polar "
                "(Dashboard → Products → ⋮ → Copy Product ID)."
            ),
        )
    # Normalize to canonical UUID string Polar expects.
    return str(UUID(product_id))


def _checkout_success_url() -> str:
    base = settings.frontend_url.strip().rstrip("/")
    if not base:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="FRONTEND_URL is not configured for Polar checkout redirects.",
        )
    parsed = urllib.parse.urlparse(base)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "FRONTEND_URL must be an absolute http(s) URL "
                "(e.g. https://opportunitymap.info)."
            ),
        )
    # Polar validates success_url as a URI; include CHECKOUT_ID for post-pay reconcile.
    return f"{base}/pricing?polar=success&checkout_id={{CHECKOUT_ID}}"


def create_checkout(db: Session, user: User) -> dict[str, str]:
    """Start Polar checkout for the configured yearly subscription product."""
    if not settings.polar_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="International checkout is not configured yet.",
        )

    product_id = _require_polar_product_id()
    success_url = _checkout_success_url()
    return_url = f"{settings.frontend_url.strip().rstrip('/')}/pricing"
    payload: dict[str, Any] = {
        "products": [product_id],
        "customer_email": user.email,
        "external_customer_id": str(user.id),
        "success_url": success_url,
        "return_url": return_url,
        "metadata": {
            "user_id": str(user.id),
            "email": user.email,
            "plan": "yearly_subscription",
        },
    }
    # Prefill billing country from profile when available (helps Polar tax / validation).
    profile = getattr(user, "profile", None)
    country = getattr(profile, "country_code", None) if profile is not None else None
    if isinstance(country, str) and len(country.strip()) == 2:
        payload["customer_billing_address"] = {"country": country.strip().upper()}

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

    return {
        "checkout_url": url,
        "checkout_id": checkout_id or None,
    }


def _checkout_belongs_to_user(checkout: dict[str, Any], user: User) -> bool:
    metadata = checkout.get("metadata") or {}
    if isinstance(metadata, dict):
        raw_user_id = metadata.get("user_id")
        if isinstance(raw_user_id, str) and raw_user_id.isdigit() and int(raw_user_id) == user.id:
            return True

    external_id = checkout.get("external_customer_id")
    if isinstance(external_id, str) and external_id.isdigit() and int(external_id) == user.id:
        return True

    email = checkout.get("customer_email")
    if isinstance(email, str) and email.strip().lower() == user.email.strip().lower():
        return True
    return False


def _map_checkout_status(polar_status: str, *, is_premium: bool) -> str:
    if is_premium:
        return "paid"
    normalized = polar_status.strip().lower()
    if normalized in {"failed", "expired"}:
        return "failed"
    if normalized in {"confirmed", "succeeded"}:
        # Confirmed at Polar but grant not applied yet (or belonging check passed
        # without an order payload) — still processing from our side.
        return "created"
    return "created"


def reconcile_checkout(db: Session, user: User, checkout_id: str) -> dict[str, Any]:
    """Fetch Polar checkout and grant premium if payment already confirmed.

    Recovers international checkouts when the browser returns before the webhook.
    """
    if not settings.polar_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="International checkout is not configured yet.",
        )

    checkout_id = checkout_id.strip()
    if not checkout_id or not _UUID_RE.match(checkout_id):
        raise HTTPException(status_code=400, detail="Invalid Polar checkout id")

    checkout = _polar_request("GET", f"/checkouts/{checkout_id}")
    if not _checkout_belongs_to_user(checkout, user):
        raise HTTPException(status_code=404, detail="Checkout not found")

    polar_status = str(checkout.get("status") or "open")
    if polar_status.lower() in {"confirmed", "succeeded"}:
        order: dict[str, Any] | None = None
        raw_order = checkout.get("order")
        if isinstance(raw_order, dict):
            order = raw_order
        else:
            order_id = checkout.get("order_id")
            if isinstance(order_id, str) and order_id.strip():
                order = _polar_request("GET", f"/orders/{order_id.strip()}")

        if order is not None:
            # Ensure metadata can resolve the paying user even if Polar omits it.
            metadata = order.get("metadata")
            if not isinstance(metadata, dict):
                metadata = {}
            metadata.setdefault("user_id", str(user.id))
            order["metadata"] = metadata
            if not order.get("external_customer_id"):
                order["external_customer_id"] = str(user.id)
            _apply_paid_order(db, order)
            db.commit()
            db.refresh(user)
        else:
            sync_premium_flag(user)
    else:
        sync_premium_flag(user)

    active = premium_is_active(user)
    return {
        "order_id": checkout_id,
        "status": _map_checkout_status(polar_status, is_premium=active),
        "is_premium": active,
        "premium_until": user.premium_until,
    }


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
