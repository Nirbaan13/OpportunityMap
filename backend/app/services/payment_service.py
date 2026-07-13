"""Razorpay yearly premium membership (₹PREMIUM_PRICE_INR / year, default 299)."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import urllib.error
import urllib.request
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.core.premium import extend_premium_year, premium_is_active, sync_premium_flag
from app.models import Payment, User


def activate_premium(db: Session, user: User, payment: Payment | None = None) -> User:
    extend_premium_year(user)
    if payment is not None:
        payment.status = "paid"
        payment.paid_at = datetime.now(UTC)
    db.commit()
    db.refresh(user)
    return user


def _razorpay_auth_header() -> str:
    raw = f"{settings.razorpay_key_id}:{settings.razorpay_key_secret}".encode()
    return "Basic " + base64.b64encode(raw).decode()


def create_razorpay_order(db: Session, user: User) -> dict:
    sync_premium_flag(user)
    if not settings.razorpay_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payments are not configured. Set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET.",
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
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        "https://api.razorpay.com/v1/orders",
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": _razorpay_auth_header(),
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            order = json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="ignore") or "Razorpay order failed"
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Razorpay error: {detail}",
        ) from exc
    except urllib.error.URLError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not reach Razorpay",
        ) from exc

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

    payment = db.scalar(
        select(Payment).where(
            Payment.user_id == user.id,
            Payment.razorpay_order_id == razorpay_order_id,
        )
    )
    if payment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment order not found",
        )
    if payment.status == "paid":
        sync_premium_flag(user)
        db.commit()
        db.refresh(user)
        return user

    payment.razorpay_payment_id = razorpay_payment_id
    payment.razorpay_signature = razorpay_signature
    return activate_premium(db, user, payment)


def dev_unlock(db: Session, user: User) -> User:
    """Local/testing unlock when Razorpay keys are not set and DEBUG=true."""
    if not settings.debug:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Dev unlock only available when DEBUG=true",
        )
    if settings.razorpay_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Use Razorpay checkout when keys are configured",
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
    return activate_premium(db, user, payment)
