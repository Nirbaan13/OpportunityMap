"""Soft auto-renew: remind members to re-purchase before their year lapses.

This does NOT charge anyone automatically. When a member has ``auto_renew``
enabled, they receive an inbox notification (and email, if SMTP is configured)
a few days before ``premium_until``. Renewing is a normal manual checkout that
extends premium by another 365 days from the current expiry.

Run daily alongside deadline reminders.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Notification, User
from app.models.enums import NotificationType
from app.services.email_service import send_email

# Days before expiry to nudge the member.
RENEWAL_LEAD_DAYS = (14, 3)


@dataclass(frozen=True)
class RenewalReminderResult:
    candidates_checked: int
    created: int
    skipped_existing: int
    emails_sent: int
    emails_failed: int


def _pricing_url() -> str:
    return f"{settings.frontend_url.rstrip('/')}/pricing"


def _already_reminded(db: Session, *, user_id: int, lead_days: int) -> bool:
    """Avoid duplicate nudges for the same expiry window.

    A 30-day lookback keeps one reminder per lead window per membership year;
    after renewal the next expiry is ~365 days away, so next year still fires.
    """
    cutoff = datetime.now(UTC) - timedelta(days=30)
    existing = db.scalar(
        select(Notification.id).where(
            Notification.user_id == user_id,
            Notification.notification_type == NotificationType.PREMIUM_RENEWAL,
            Notification.reminder_lead_days == lead_days,
            Notification.created_at >= cutoff,
        )
    )
    return existing is not None


def _build_copy(days_left: int, expires_on: str) -> tuple[str, str]:
    title = f"Premium renews in {days_left} day{'s' if days_left != 1 else ''}"
    message = (
        f"Your OpportunityMap Premium year ends on {expires_on}. "
        "Renew to keep your profile, matches, saved opportunities, and alerts. "
        "Renewing early adds another 365 days on top of your current time."
    )
    return title, message


def _build_email(title: str, message: str) -> tuple[str, str]:
    url = _pricing_url()
    text_body = f"{message}\n\nRenew: {url}\n\n— OpportunityMap\n"
    html_body = (
        '<html><body style="font-family: system-ui, sans-serif; line-height: 1.5; '
        'color: #1a1a1a;">'
        f"<p>{message}</p>"
        f'<p><a href="{url}">Renew your membership</a></p>'
        '<p style="color:#666;font-size:12px;">You receive this because auto-renew '
        "reminders are on. Turn them off anytime from your profile.</p>"
        "</body></html>"
    )
    return text_body, html_body


def run_renewal_reminders(
    db: Session,
    *,
    now: datetime | None = None,
) -> RenewalReminderResult:
    now = now or datetime.now(UTC)

    created = 0
    skipped = 0
    candidates = 0
    pending: list[tuple[str, str, str, str]] = []

    for lead_days in RENEWAL_LEAD_DAYS:
        window_start = now + timedelta(days=lead_days)
        window_end = now + timedelta(days=lead_days + 1)
        users = list(
            db.scalars(
                select(User).where(
                    User.is_active.is_(True),
                    User.auto_renew.is_(True),
                    User.premium_until.is_not(None),
                    User.premium_until >= window_start,
                    User.premium_until < window_end,
                )
            ).all()
        )
        for user in users:
            candidates += 1
            if _already_reminded(db, user_id=user.id, lead_days=lead_days):
                skipped += 1
                continue
            assert user.premium_until is not None
            expires_on = user.premium_until.astimezone(UTC).strftime("%Y-%m-%d")
            title, message = _build_copy(lead_days, expires_on)
            db.add(
                Notification(
                    user_id=user.id,
                    opportunity_id=None,
                    notification_type=NotificationType.PREMIUM_RENEWAL,
                    title=title,
                    message=message,
                    is_read=False,
                    reminder_lead_days=lead_days,
                )
            )
            created += 1
            text_body, html_body = _build_email(title, message)
            pending.append((user.email, title, text_body, html_body))

    db.commit()

    emails_sent = 0
    emails_failed = 0
    for to_email, subject, text_body, html_body in pending:
        ok = send_email(
            to_email=to_email,
            subject=subject,
            text_body=text_body,
            html_body=html_body,
        )
        if ok:
            emails_sent += 1
        else:
            emails_failed += 1

    return RenewalReminderResult(
        candidates_checked=candidates,
        created=created,
        skipped_existing=skipped,
        emails_sent=emails_sent,
        emails_failed=emails_failed,
    )
