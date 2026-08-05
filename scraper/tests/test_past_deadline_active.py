"""Past-deadline opportunities must not stay in the active feed."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from scraper.parsers.dates import deadline_is_upcoming
from scraper.repository import _is_active_for_deadline


def test_past_deadline_is_not_active() -> None:
    past = datetime.now(UTC) - timedelta(days=1)
    assert deadline_is_upcoming(past) is False
    assert _is_active_for_deadline(past) is False


def test_future_and_undated_stay_active() -> None:
    future = datetime.now(UTC) + timedelta(days=10)
    assert _is_active_for_deadline(future) is True
    assert _is_active_for_deadline(None) is True
