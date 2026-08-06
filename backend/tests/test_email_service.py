"""Email helper behaviour for deliverability."""

from __future__ import annotations

from app.config import settings
from app.services import email_service


def test_from_header_prefers_smtp_username(monkeypatch) -> None:
    monkeypatch.setattr(settings, "smtp_from", "OpportunityMap <other@example.com>")
    monkeypatch.setattr(settings, "smtp_username", "founder.opportunitymap@gmail.com")
    header = email_service._from_header()
    assert "founder.opportunitymap@gmail.com" in header
    assert "OpportunityMap" in header


def test_list_unsubscribe_includes_site(monkeypatch) -> None:
    monkeypatch.setattr(settings, "frontend_url", "https://opportunitymap.info")
    monkeypatch.setattr(settings, "smtp_username", "founder.opportunitymap@gmail.com")
    headers = email_service._list_unsubscribe_headers()
    assert "List-Unsubscribe" in headers
    assert "https://opportunitymap.info/notifications" in headers["List-Unsubscribe"]
