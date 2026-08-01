"""Founder admin aggregates — user counts, premium, payments."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models import Opportunity, Payment, Profile, User


def build_admin_overview(db: Session) -> dict:
    now = datetime.now(UTC)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    users_total = db.scalar(select(func.count()).select_from(User)) or 0
    active_users = (
        db.scalar(select(func.count()).select_from(User).where(User.is_active.is_(True))) or 0
    )
    premium_users = (
        db.scalar(
            select(func.count())
            .select_from(User)
            .where(
                User.is_premium.is_(True),
                (User.premium_until.is_(None)) | (User.premium_until >= now),
            )
        )
        or 0
    )
    users_with_profile = db.scalar(select(func.count()).select_from(Profile)) or 0
    signups_7 = (
        db.scalar(select(func.count()).select_from(User).where(User.created_at >= week_ago)) or 0
    )
    signups_30 = (
        db.scalar(select(func.count()).select_from(User).where(User.created_at >= month_ago)) or 0
    )
    logins_7 = (
        db.scalar(
            select(func.count())
            .select_from(User)
            .where(User.last_login_at.is_not(None), User.last_login_at >= week_ago)
        )
        or 0
    )
    logins_30 = (
        db.scalar(
            select(func.count())
            .select_from(User)
            .where(User.last_login_at.is_not(None), User.last_login_at >= month_ago)
        )
        or 0
    )

    opportunities_total = db.scalar(select(func.count()).select_from(Opportunity)) or 0
    opportunities_active = (
        db.scalar(
            select(func.count()).select_from(Opportunity).where(Opportunity.is_active.is_(True))
        )
        or 0
    )

    payments_paid = (
        db.scalar(select(func.count()).select_from(Payment).where(Payment.status == "paid")) or 0
    )
    payments_created = (
        db.scalar(select(func.count()).select_from(Payment).where(Payment.status == "created"))
        or 0
    )

    paid_inr_paise = (
        db.scalar(
            select(func.coalesce(func.sum(Payment.amount_paise), 0)).where(
                Payment.status == "paid",
                Payment.currency == "INR",
            )
        )
        or 0
    )
    # USD amounts may be stored as cents in amount_paise for Polar
    paid_usd_cents = (
        db.scalar(
            select(func.coalesce(func.sum(Payment.amount_paise), 0)).where(
                Payment.status == "paid",
                Payment.currency == "USD",
            )
        )
        or 0
    )

    status_rows = db.execute(
        select(Payment.status, func.count())
        .group_by(Payment.status)
        .order_by(func.count().desc())
    ).all()
    provider_rows = db.execute(
        select(Payment.provider, func.count())
        .group_by(Payment.provider)
        .order_by(func.count().desc())
    ).all()

    recent_users = list(
        db.scalars(
            select(User)
            .options(joinedload(User.profile))
            .order_by(User.created_at.desc(), User.id.desc())
            .limit(40)
        )
        .unique()
        .all()
    )

    recent_payments = list(
        db.scalars(
            select(Payment)
            .options(joinedload(Payment.user))
            .order_by(Payment.created_at.desc(), Payment.id.desc())
            .limit(40)
        )
        .unique()
        .all()
    )

    return {
        "totals": {
            "users": users_total,
            "active_users": active_users,
            "premium_users": premium_users,
            "users_with_profile": users_with_profile,
            "signups_last_7_days": signups_7,
            "signups_last_30_days": signups_30,
            "logins_last_7_days": logins_7,
            "logins_last_30_days": logins_30,
            "opportunities_active": opportunities_active,
            "opportunities_total": opportunities_total,
            "payments_paid": payments_paid,
            "payments_created": payments_created,
            "paid_amount_inr": round(int(paid_inr_paise) / 100, 2),
            "paid_amount_usd": round(int(paid_usd_cents) / 100, 2),
        },
        "payments_by_status": [{"key": row[0], "count": row[1]} for row in status_rows],
        "payments_by_provider": [{"key": row[0], "count": row[1]} for row in provider_rows],
        "recent_users": [
            {
                "id": user.id,
                "email": user.email,
                "is_active": user.is_active,
                "is_premium": bool(
                    user.is_premium
                    and (user.premium_until is None or user.premium_until >= now)
                ),
                "premium_until": user.premium_until,
                "has_profile": user.profile is not None,
                "created_at": user.created_at,
                "last_login_at": user.last_login_at,
            }
            for user in recent_users
        ],
        "recent_payments": [
            {
                "id": payment.id,
                "user_id": payment.user_id,
                "user_email": payment.user.email,
                "provider": payment.provider,
                "status": payment.status,
                "amount": round(payment.amount_paise / 100, 2),
                "currency": payment.currency,
                "created_at": payment.created_at,
                "paid_at": payment.paid_at,
            }
            for payment in recent_payments
        ],
    }
