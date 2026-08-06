"""Send email via SMTP (stdlib). Used for deadline reminders to registered addresses."""

from __future__ import annotations

import logging
import re
import smtplib
import time
import uuid
from email.message import EmailMessage
from email.utils import formataddr, formatdate, make_msgid, parseaddr

from app.config import settings

logger = logging.getLogger(__name__)

# Space bulk reminder sends so Gmail is less likely to treat them as a burst.
_MIN_SEND_GAP_SECONDS = 2.5
_last_send_monotonic: float | None = None


def _pace_sends() -> None:
    """Wait between consecutive SMTP sends in the same process."""
    global _last_send_monotonic
    now = time.monotonic()
    if _last_send_monotonic is not None:
        wait = _MIN_SEND_GAP_SECONDS - (now - _last_send_monotonic)
        if wait > 0:
            time.sleep(wait)
    _last_send_monotonic = time.monotonic()


def _from_header() -> str:
    """Prefer a display-name From that matches the authenticated mailbox."""
    raw = (settings.smtp_from or "").strip()
    name, addr = parseaddr(raw)
    if not addr and "@" in raw:
        addr = raw
    auth_user = (settings.smtp_username or "").strip()
    # Gmail is less spammy when From matches the logged-in account.
    if auth_user and "@" in auth_user:
        addr = auth_user
    display = name or "OpportunityMap"
    return formataddr((display, addr)) if addr else raw


def _list_unsubscribe_headers() -> dict[str, str]:
    base = (settings.frontend_url or "").rstrip("/")
    if not base:
        return {}
    # One-click style mailto + HTTPS preference helps inbox placement.
    mailto = settings.smtp_username.strip() or "founder.opportunitymap@gmail.com"
    return {
        "List-Unsubscribe": f"<mailto:{mailto}?subject=unsubscribe>, <{base}/notifications>",
        "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
    }


def send_email(*, to_email: str, subject: str, text_body: str, html_body: str | None = None) -> bool:
    """
    Send one email to ``to_email``.

    Returns True on success. If SMTP is not configured, logs and returns False
    without raising (inbox notifications still work).
    """
    if not settings.email_enabled:
        logger.info("SMTP not configured; skipped email to %s (%s)", to_email, subject)
        return False

    clean_subject = re.sub(r"\s+", " ", (subject or "").strip())[:180]
    message = EmailMessage()
    message["Subject"] = clean_subject
    message["From"] = _from_header()
    message["To"] = to_email
    message["Date"] = formatdate(localtime=False)
    message["Message-ID"] = make_msgid(domain="opportunitymap.info")
    message["MIME-Version"] = "1.0"
    message["X-Mailer"] = "OpportunityMap"
    message["X-Entity-Ref-ID"] = str(uuid.uuid4())
    reply = (settings.smtp_username or "").strip()
    if reply:
        message["Reply-To"] = reply
    for key, value in _list_unsubscribe_headers().items():
        message[key] = value

    # Plain text first; HTML as alternative — better for spam filters than HTML-only.
    message.set_content(text_body or clean_subject)
    if html_body:
        message.add_alternative(html_body, subtype="html")

    try:
        _pace_sends()
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as smtp:
            if settings.smtp_use_tls:
                smtp.starttls()
            if settings.smtp_username:
                smtp.login(settings.smtp_username, settings.smtp_password)
            smtp.send_message(message)
        logger.info("Sent email to %s: %s", to_email, clean_subject)
        return True
    except Exception:
        logger.exception("Failed to send email to %s: %s", to_email, clean_subject)
        return False
