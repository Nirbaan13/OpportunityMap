"""Yearly premium membership helpers."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.models import User

PREMIUM_DAYS = 365


def premium_is_active(user: User, *, now: datetime | None = None) -> bool:
    now = now or datetime.now(UTC)
    if user.premium_until is None:
        return False
    until = user.premium_until
    if until.tzinfo is None:
        until = until.replace(tzinfo=UTC)
    return until >= now


def sync_premium_flag(user: User, *, now: datetime | None = None) -> bool:
    """Update denormalized is_premium from premium_until. Returns active status."""
    active = premium_is_active(user, now=now)
    user.is_premium = active
    return active


def extend_premium_year(user: User, *, now: datetime | None = None) -> datetime:
    """Extend membership by 365 days from now or current expiry (whichever is later)."""
    now = now or datetime.now(UTC)
    if user.premium_activated_at is None:
        user.premium_activated_at = now

    current_until = user.premium_until
    if current_until is not None and current_until.tzinfo is None:
        current_until = current_until.replace(tzinfo=UTC)

    base = now
    if current_until is not None and current_until > now:
        base = current_until

    user.premium_until = base + timedelta(days=PREMIUM_DAYS)
    user.is_premium = True
    return user.premium_until
