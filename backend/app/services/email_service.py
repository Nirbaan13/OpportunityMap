"""Send email via SMTP (stdlib). Used for deadline reminders to registered addresses."""

from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from app.config import settings

logger = logging.getLogger(__name__)


def send_email(*, to_email: str, subject: str, text_body: str, html_body: str | None = None) -> bool:
    """
    Send one email to ``to_email``.

    Returns True on success. If SMTP is not configured, logs and returns False
    without raising (inbox notifications still work).
    """
    if not settings.email_enabled:
        logger.info("SMTP not configured; skipped email to %s (%s)", to_email, subject)
        return False

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.smtp_from
    message["To"] = to_email
    message.set_content(text_body)
    if html_body:
        message.add_alternative(html_body, subtype="html")

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as smtp:
            if settings.smtp_use_tls:
                smtp.starttls()
            if settings.smtp_username:
                smtp.login(settings.smtp_username, settings.smtp_password)
            smtp.send_message(message)
        logger.info("Sent email to %s: %s", to_email, subject)
        return True
    except Exception:
        logger.exception("Failed to send email to %s: %s", to_email, subject)
        return False
