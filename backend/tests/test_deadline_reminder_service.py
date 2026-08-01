"""Unit tests for deadline reminder lead-day scheduling."""

from datetime import UTC, datetime

from app.services.deadline_reminder_service import (
    _days_until,
    _interest_schedule,
    _remind_me_schedule,
)


def test_days_until_utc_calendar() -> None:
    now = datetime(2026, 7, 31, 15, 0, tzinfo=UTC)
    deadline = datetime(2026, 8, 10, 12, 0, tzinfo=UTC)
    assert _days_until(deadline, now) == 10


def test_remind_me_exact_and_catchup() -> None:
    assert _remind_me_schedule(1) == (1, 1)
    assert _remind_me_schedule(10) == (10, 10)
    assert _remind_me_schedule(2) == (10, 2)
    assert _remind_me_schedule(9) == (10, 9)
    assert _remind_me_schedule(11) is None
    assert _remind_me_schedule(0) is None
    assert _remind_me_schedule(30) is None


def test_interest_exact_and_catchup() -> None:
    assert _interest_schedule(90) == (90, 90)
    assert _interest_schedule(89) == (90, 89)
    assert _interest_schedule(88) == (90, 88)
    assert _interest_schedule(87) is None
    assert _interest_schedule(91) is None

    assert _interest_schedule(30) == (30, 30)
    assert _interest_schedule(29) == (30, 29)
    assert _interest_schedule(28) == (30, 28)
    assert _interest_schedule(27) is None
    assert _interest_schedule(31) is None
