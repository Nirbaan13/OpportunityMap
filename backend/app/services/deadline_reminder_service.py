"""Create deadline reminders: website inbox + optional email.

Lead windows:
  - Interest overlap (premium + profile eligibility):
      * ~90 days: exact day 90, or catch-up if the job missed days 88–89
      * ~30 days: exact day 30, or catch-up if the job missed days 28–29
      → inbox + email when SMTP is configured
  - Remind me (premium): ~30 days, day 10, and day 1 (plus catch-up)
      → inbox + email
  - Remind me (free): ~30 days only (28–30 catch-up), inbox only — no email

Run daily (cron / Task Scheduler):

  cd backend
  .\\.venv\\Scripts\\Activate.ps1
  python -m app.jobs.run_deadline_reminders
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session, joinedload

from app.config import settings
from app.models import Bookmark, Notification, Opportunity, Profile, User
from app.models.enums import NotificationType
from app.models.profile import profile_fields
from app.services.email_service import send_email

# Early awareness: interest overlap (dedupe keys) — premium only
INTEREST_LEAD_DAYS = (90, 30)
# Catch-up span after a missed exact day (inclusive of the exact lead day).
INTEREST_CATCHUP_SLACK = 2
# Close deadlines: premium Remind me (dedupe keys) — month + week + day
REMIND_ME_LEAD_DAYS = (30, 10, 1)
# Free Remind me: one month out only
FREE_REMIND_LEAD_DAYS = 30


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
    notification_id: int | None = None


def _days_until(deadline: datetime, now: datetime) -> int:
    d = deadline.astimezone(UTC).date() if deadline.tzinfo else deadline.replace(tzinfo=UTC).date()
    n = now.astimezone(UTC).date()
    return (d - n).days


def _interest_schedule(days_left: int) -> tuple[int, int] | None:
    """Return ``(dedupe_lead_days, display_days)`` for interest alerts, or None."""
    for lead in INTEREST_LEAD_DAYS:
        if lead - INTEREST_CATCHUP_SLACK <= days_left <= lead:
            return (lead, days_left)
    return None


def _remind_me_schedule(days_left: int) -> tuple[int, int] | None:
    """Premium Remind me: ~30 days, ~10 days (2–10 catch-up), or exact 1 day."""
    if days_left == 1:
        return (1, 1)
    if 2 <= days_left <= 10:
        return (10, days_left)
    lead = FREE_REMIND_LEAD_DAYS
    if lead - INTEREST_CATCHUP_SLACK <= days_left <= lead:
        return (lead, days_left)
    return None


def _free_remind_me_schedule(days_left: int) -> tuple[int, int] | None:
    """Free Remind me: ~30 days only (28–30 catch-up), deduped as 30."""
    lead = FREE_REMIND_LEAD_DAYS
    if lead - INTEREST_CATCHUP_SLACK <= days_left <= lead:
        return (lead, days_left)
    return None


def _lead_label(lead_days: int) -> str:
    if lead_days == 90:
        return "about 3 months"
    if lead_days == 1:
        return "1 day"
    return f"{lead_days} days"


def _opportunity_url(opportunity_id: int) -> str:
    base = settings.frontend_url.rstrip("/")
    return f"{base}/opportunities/{opportunity_id}"


def _build_copy(opportunity: Opportunity, display_days: int) -> tuple[str, str]:
    label = _lead_label(display_days)
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


def _find_reminder(
    db: Session,
    *,
    user_id: int,
    opportunity_id: int,
    lead_days: int,
) -> Notification | None:
    return db.scalar(
        select(Notification).where(
            Notification.user_id == user_id,
            Notification.opportunity_id == opportunity_id,
            Notification.notification_type == NotificationType.DEADLINE_REMINDER,
            Notification.reminder_lead_days == lead_days,
        )
    )


def _pending_mail_for(
    *,
    to_email: str,
    opportunity: Opportunity,
    lead_days: int,
    title: str,
    message: str,
    notification_id: int | None,
) -> _PendingMail:
    subject, text_body, html_body = _build_email(
        opportunity, lead_days, title=title, message=message
    )
    return _PendingMail(
        to_email=to_email,
        subject=subject,
        text_body=text_body,
        html_body=html_body,
        notification_id=notification_id,
    )


def _create_reminder(
    db: Session,
    *,
    user_id: int,
    to_email: str,
    opportunity: Opportunity,
    lead_days: int,
    display_days: int | None = None,
    send_email_to_user: bool = True,
) -> tuple[bool, _PendingMail | None]:
    """Return ``(created, pending_mail)``.

    If an inbox alert already exists without email (e.g. free Remind me, then
    premium upgrade), queue the email without creating a duplicate notification.
    """
    existing = _find_reminder(
        db,
        user_id=user_id,
        opportunity_id=opportunity.id,
        lead_days=lead_days,
    )
    shown = display_days if display_days is not None else lead_days
    title, message = _build_copy(opportunity, shown)

    if existing is not None:
        if send_email_to_user and not existing.email_sent:
            return False, _pending_mail_for(
                to_email=to_email,
                opportunity=opportunity,
                lead_days=lead_days,
                title=existing.title or title,
                message=existing.message or message,
                notification_id=existing.id,
            )
        return False, None

    row = Notification(
        user_id=user_id,
        opportunity_id=opportunity.id,
        notification_type=NotificationType.DEADLINE_REMINDER,
        title=title,
        message=message,
        is_read=False,
        reminder_lead_days=lead_days,
        email_sent=False,
    )
    db.add(row)
    db.flush()
    if not send_email_to_user:
        return True, None
    return True, _pending_mail_for(
        to_email=to_email,
        opportunity=opportunity,
        lead_days=lead_days,
        title=title,
        message=message,
        notification_id=row.id,
    )


def _premium_active_clause(now: datetime):
    return and_(
        User.premium_until.is_not(None),
        User.premium_until >= now,
    )


def _free_tier_clause(now: datetime):
    """Active account that is not currently premium."""
    return and_(
        User.is_active.is_(True),
        or_(User.premium_until.is_(None), User.premium_until < now),
    )


def _interest_recipients(db: Session, opportunity: Opportunity, *, now: datetime) -> list[tuple[int, str]]:
    """Premium users with interest overlap + eligibility."""
    field_ids = [field.id for field in opportunity.fields]
    if not field_ids:
        return []

    grade_min = opportunity.grade_min
    grade_max = opportunity.grade_max
    countries = opportunity.eligible_countries

    conditions = [
        User.is_active.is_(True),
        _premium_active_clause(now),
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


def _remind_me_recipients(
    db: Session,
    opportunity_id: int,
    *,
    now: datetime,
    premium: bool,
) -> list[tuple[int, str]]:
    tier = _premium_active_clause(now) if premium else _free_tier_clause(now)
    stmt = (
        select(User.id, User.email)
        .join(Bookmark, Bookmark.user_id == User.id)
        .where(
            Bookmark.opportunity_id == opportunity_id,
            Bookmark.remind_me.is_(True),
            User.is_active.is_(True),
            tier,
        )
    )
    return list(db.execute(stmt).all())


def run_deadline_reminders(
    db: Session,
    *,
    now: datetime | None = None,
) -> ReminderRunResult:
    """Create due inbox notifications; email premium recipients when SMTP is set."""
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
        # (lead_days, display_days, recipients, send_email)
        batches: list[tuple[int, int, list[tuple[int, str]], bool]] = []

        interest = _interest_schedule(days_left)
        if interest is not None:
            dedupe_lead, display_days = interest
            batches.append(
                (
                    dedupe_lead,
                    display_days,
                    _interest_recipients(db, opportunity, now=now),
                    True,
                )
            )

        remind = _remind_me_schedule(days_left)
        if remind is not None:
            dedupe_lead, display_days = remind
            batches.append(
                (
                    dedupe_lead,
                    display_days,
                    _remind_me_recipients(db, opportunity.id, now=now, premium=True),
                    True,
                )
            )

        free_remind = _free_remind_me_schedule(days_left)
        if free_remind is not None:
            dedupe_lead, display_days = free_remind
            batches.append(
                (
                    dedupe_lead,
                    display_days,
                    _remind_me_recipients(db, opportunity.id, now=now, premium=False),
                    False,
                )
            )

        for lead_days, display_days, recipients, send_mail in batches:
            for user_id, email in recipients:
                was_created, mail = _create_reminder(
                    db,
                    user_id=user_id,
                    to_email=email,
                    opportunity=opportunity,
                    lead_days=lead_days,
                    display_days=display_days,
                    send_email_to_user=send_mail,
                )
                if was_created:
                    created += 1
                if mail is not None:
                    pending_mail.append(mail)
                elif not was_created:
                    skipped += 1

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
            if mail.notification_id is not None:
                row = db.get(Notification, mail.notification_id)
                if row is not None:
                    row.email_sent = True
        else:
            emails_failed += 1

    if emails_sent:
        db.commit()

    return ReminderRunResult(
        opportunities_checked=len(opportunities),
        created=created,
        skipped_existing=skipped,
        emails_sent=emails_sent,
        emails_failed=emails_failed,
    )
