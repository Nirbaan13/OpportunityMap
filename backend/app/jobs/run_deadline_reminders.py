"""CLI: create due deadline reminders (website inbox + registered email).

Usage (from backend/ with venv active):

  python -m app.jobs.run_deadline_reminders

Configure SMTP in backend/.env (SMTP_HOST, SMTP_FROM, …). Without SMTP,
inbox rows are still created; emails are skipped.
"""

from __future__ import annotations

from app.config import settings
from app.database import SessionLocal
from app.services.deadline_reminder_service import run_deadline_reminders
from app.services.renewal_reminder_service import run_renewal_reminders


def main() -> None:
    db = SessionLocal()
    try:
        result = run_deadline_reminders(db)
        print(
            f"Checked {result.opportunities_checked} opportunities; "
            f"created {result.created} notifications; "
            f"skipped {result.skipped_existing} already-sent; "
            f"emails sent {result.emails_sent}, failed/skipped {result.emails_failed}."
        )
        renewal = run_renewal_reminders(db)
        print(
            f"Renewal reminders: checked {renewal.candidates_checked}; "
            f"created {renewal.created}; skipped {renewal.skipped_existing}; "
            f"emails sent {renewal.emails_sent}, failed/skipped {renewal.emails_failed}."
        )
        if (result.created or renewal.created) and not settings.email_enabled:
            print(
                "Note: SMTP is not configured (set SMTP_HOST and SMTP_FROM). "
                "Inbox alerts were saved; no mail was sent."
            )
    finally:
        db.close()


if __name__ == "__main__":
    main()
