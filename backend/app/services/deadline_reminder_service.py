"""Create deadline reminders: website inbox + email to registered address.

Lead windows:
  - 90 days (≈ 3 months) and 30 days → students with overlapping interests
    (and hard eligibility: grade + country), who have a profile.
  - 10 days and 1 day → only students who opted into Remind me on that opportunity.

Each new reminder is stored in ``notifications`` and emailed to ``users.email``
when SMTP is configured.

Run daily (cron / Task Scheduler):

  cd backend
  .\\.venv\\Scripts\\Activate.ps1
  python -m app.jobs.run_deadline_reminders
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.config import settings
from app.models import Bookmark, Notification, Opportunity, Profile, User
from app.models.enums import NotificationType
from app.models.profile import profile_fields
from app.services.email_service import send_email

# Early awareness: interest overlap
INTEREST_LEAD_DAYS = (90, 30)
# Close deadlines: explicit Remind me opt-in
REMIND_ME_LEAD_DAYS = (10, 1)
ALL_LEAD_DAYS = INTEREST_LEAD_DAYS + REMIND_ME_LEAD_DAYS


@dataclass(frozen=True)
class ReminderRunResult:
    opportunities_checked: int
    created: int
    skipped_existing: int
    emails_sent: int
    emails_failed: int


@dataclass(frozen=True)
class _PendingMail:
    to_email: str
    subject: str
    text_body: str
    html_body: str


def _days_until(deadline: datetime, now: datetime) -> int:
    d = deadline.astimezone(UTC).date() if deadline.tzinfo else deadline.replace(tzinfo=UTC).date()
    n = now.astimezone(UTC).date()
    return (d - n).days


def _lead_label(lead_days: int) -> str:
    if lead_days == 90:
        return "about 3 months"
    if lead_days == 1:
        return "1 day"
    return f"{lead_days} days"


def _opportunity_url(opportunity_id: int) -> str:
    base = settings.frontend_url.rstrip("/")
    return f"{base}/opportunities/{opportunity_id}"


def _build_copy(opportunity: Opportunity, lead_days: int) -> tuple[str, str]:
    label = _lead_label(lead_days)
    title = f"Deadline in {label}: {opportunity.title}"
    if len(title) > 200:
        title = title[:197] + "..."
    deadline_text = (
        opportunity.deadline_at.astimezone(UTC).strftime("%Y-%m-%d")
        if opportunity.deadline_at
        else "soon"
    )
    message = (
        f'"{opportunity.title}" closes in {label} (deadline {deadline_text}). '
        "Open OpportunityMap to review details and apply."
    )
    return title, message


def _build_email(
    opportunity: Opportunity,
    lead_days: int,
    *,
    title: str,
    message: str,
) -> tuple[str, str, str]:
    url = _opportunity_url(opportunity.id)
    text_body = (
        f"{message}\n\n"
        f"View opportunity: {url}\n"
        f"Your alerts inbox: {settings.frontend_url.rstrip('/')}/notifications\n\n"
        "— OpportunityMap\n"
    )
    html_body = f"""\
<html><body style="font-family: system-ui, sans-serif; line-height: 1.5; color: #1a1a1a;">
  <p>{message}</p>
  <p><a href="{url}">View opportunity</a> · <a href="{settings.frontend_url.rstrip("/")}/notifications">Open alerts</a></p>
  <p style="color:#666;font-size:12px;">You received this because you registered on OpportunityMap
  {"and share interests with this opportunity" if lead_days in INTEREST_LEAD_DAYS else "and turned on Remind me for this opportunity"}.</p>
</body></html>
"""
    return title, text_body, html_body


def _already_sent(
    db: Session,
    *,
    user_id: int,
    opportunity_id: int,
    lead_days: int,
) -> bool:
    existing = db.scalar(
        select(Notification.id).where(
            Notification.user_id == user_id,
            Notification.opportunity_id == opportunity_id,
            Notification.notification_type == NotificationType.DEADLINE_REMINDER,
            Notification.reminder_lead_days == lead_days,
        )
    )
    return existing is not None


def _create_reminder(
    db: Session,
    *,
    user_id: int,
    to_email: str,
    opportunity: Opportunity,
    lead_days: int,
) -> _PendingMail | None:
    if _already_sent(
        db,
        user_id=user_id,
        opportunity_id=opportunity.id,
        lead_days=lead_days,
    ):
        return None
    title, message = _build_copy(opportunity, lead_days)
    db.add(
        Notification(
            user_id=user_id,
            opportunity_id=opportunity.id,
            notification_type=NotificationType.DEADLINE_REMINDER,
            title=title,
            message=message,
            is_read=False,
            reminder_lead_days=lead_days,
        )
    )
    subject, text_body, html_body = _build_email(
        opportunity, lead_days, title=title, message=message
    )
    return _PendingMail(
        to_email=to_email,
        subject=subject,
        text_body=text_body,
        html_body=html_body,
    )


def _interest_recipients(db: Session, opportunity: Opportunity) -> list[tuple[int, str]]:
    """(user_id, email) for interest-overlap + eligibility."""
    field_ids = [field.id for field in opportunity.fields]
    if not field_ids:
        return []

    grade_min = opportunity.grade_min
    grade_max = opportunity.grade_max
    countries = opportunity.eligible_countries

    conditions = [
        User.is_active.is_(True),
        User.premium_until.is_not(None),
        User.premium_until >= datetime.now(UTC),
    ]
    if grade_min is not None:
        conditions.append(Profile.grade_level >= grade_min)
    if grade_max is not None:
        conditions.append(Profile.grade_level <= grade_max)
    if countries:
        conditions.append(Profile.country_code.in_([c.upper() for c in countries]))

    stmt = (
        select(User.id, User.email)
        .join(Profile, Profile.user_id == User.id)
        .where(*conditions)
        .where(
            Profile.id.in_(
                select(profile_fields.c.profile_id).where(
                    profile_fields.c.field_id.in_(field_ids)
                )
            )
        )
        .distinct()
    )
    return list(db.execute(stmt).all())


def _remind_me_recipients(db: Session, opportunity_id: int) -> list[tuple[int, str]]:
    stmt = (
        select(User.id, User.email)
        .join(Bookmark, Bookmark.user_id == User.id)
        .where(
            Bookmark.opportunity_id == opportunity_id,
            Bookmark.remind_me.is_(True),
                User.is_active.is_(True),
                User.premium_until.is_not(None),
                User.premium_until >= datetime.now(UTC),
        )
    )
    return list(db.execute(stmt).all())


def run_deadline_reminders(
    db: Session,
    *,
    now: datetime | None = None,
) -> ReminderRunResult:
    """Create due inbox notifications and email each recipient's registered address."""
    now = now or datetime.now(UTC)
    opportunities = list(
        db.scalars(
            select(Opportunity)
            .options(joinedload(Opportunity.fields))
            .where(Opportunity.is_active.is_(True))
            .where(Opportunity.deadline_at.is_not(None))
            .where(Opportunity.deadline_at >= now)
        )
        .unique()
        .all()
    )

    created = 0
    skipped = 0
    pending_mail: list[_PendingMail] = []

    for opportunity in opportunities:
        assert opportunity.deadline_at is not None
        days_left = _days_until(opportunity.deadline_at, now)
        if days_left not in ALL_LEAD_DAYS:
            continue

        if days_left in INTEREST_LEAD_DAYS:
            recipients = _interest_recipients(db, opportunity)
        else:
            recipients = _remind_me_recipients(db, opportunity.id)

        for user_id, email in recipients:
            mail = _create_reminder(
                db,
                user_id=user_id,
                to_email=email,
                opportunity=opportunity,
                lead_days=days_left,
            )
            if mail is None:
                skipped += 1
            else:
                created += 1
                pending_mail.append(mail)

    db.commit()

    emails_sent = 0
    emails_failed = 0
    for mail in pending_mail:
        ok = send_email(
            to_email=mail.to_email,
            subject=mail.subject,
            text_body=mail.text_body,
            html_body=mail.html_body,
        )
        if ok:
            emails_sent += 1
        else:
            emails_failed += 1

    return ReminderRunResult(
        opportunities_checked=len(opportunities),
        created=created,
        skipped_existing=skipped,
        emails_sent=emails_sent,
        emails_failed=emails_failed,
    )
