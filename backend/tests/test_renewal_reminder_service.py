from app.services.renewal_reminder_service import (
    RENEWAL_LEAD_DAYS,
    _build_copy,
    _build_email,
)


def test_renewal_lead_windows_are_before_expiry() -> None:
    # Reminders should fire a couple of times, and always before expiry.
    assert RENEWAL_LEAD_DAYS == (14, 3)
    assert all(days > 0 for days in RENEWAL_LEAD_DAYS)


def test_renewal_copy_mentions_days_and_date() -> None:
    title, message = _build_copy(3, "2026-08-01")
    assert "3 days" in title
    assert "2026-08-01" in message
    # It must make clear this is a manual renewal, not an automatic charge.
    assert "365 days" in message


def test_renewal_copy_singular_day() -> None:
    title, _ = _build_copy(1, "2026-08-01")
    assert "1 day" in title
    assert "1 days" not in title


def test_renewal_email_links_to_pricing() -> None:
    text_body, html_body = _build_email("Renew soon", "Your year ends soon.")
    assert "/pricing" in text_body
    assert "/pricing" in html_body
