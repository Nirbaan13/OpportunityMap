"""Auth email normalization and rate-limit unit tests."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.core.emails import normalize_email
from app.core.rate_limit import check_rate_limit, reset_rate_limits_for_tests
from app.services.auth_service import authenticate_user, register_user


def test_normalize_email() -> None:
    assert normalize_email("  Foo.Bar@Example.COM ") == "foo.bar@example.com"


def test_rate_limit_blocks_after_threshold() -> None:
    reset_rate_limits_for_tests()
    for _ in range(3):
        check_rate_limit(key="test:ip", limit=3, window_seconds=60)
    with pytest.raises(HTTPException) as exc:
        check_rate_limit(key="test:ip", limit=3, window_seconds=60)
    assert exc.value.status_code == 429


def test_register_stores_lowercase_email(monkeypatch: pytest.MonkeyPatch) -> None:
    db = MagicMock()
    # No existing user
    db.scalar.return_value = None

    captured: dict = {}

    def fake_add(user):
        captured["email"] = user.email
        user.id = 1

    db.add.side_effect = fake_add
    db.commit.return_value = None
    db.refresh.side_effect = lambda u: None

    monkeypatch.setattr(
        "app.services.auth_service.hash_password", lambda p: "hashed"
    )
    user = register_user(db, "Student@Example.COM", "password123")
    assert captured["email"] == "student@example.com"
    assert user.email == "student@example.com"


def test_authenticate_accepts_mixed_case_and_heals(monkeypatch: pytest.MonkeyPatch) -> None:
    stored = SimpleNamespace(
        id=1,
        email="Student@Example.COM",
        password_hash="hashed",
        is_active=True,
    )
    db = MagicMock()
    db.scalar.return_value = stored

    monkeypatch.setattr(
        "app.services.auth_service.verify_password", lambda plain, hashed: True
    )
    monkeypatch.setattr(
        "app.services.auth_service.create_access_token",
        lambda subject: f"token-for-{subject}",
    )

    token = authenticate_user(db, "student@example.com", "password123")
    assert stored.email == "student@example.com"
    assert token == "token-for-student@example.com"
    db.commit.assert_called()
