from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.config import Settings, settings
from app.models import User
from app.services.payment_service import recompute_premium, verify_webhook_signature


class _ScalarResult:
    def __init__(self, values: list[object]) -> None:
        self.values = values

    def all(self) -> list[object]:
        return self.values


class _GrantSession:
    def __init__(self, grants: list[object]) -> None:
        self.grants = grants

    def scalars(self, _statement: object) -> _ScalarResult:
        return _ScalarResult(self.grants)


def test_webhook_signature_uses_raw_body(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "razorpay_webhook_secret", "webhook-secret")
    raw_body = b'{"event":"payment.captured","payload":{"value":1}}'

    import hashlib
    import hmac

    signature = hmac.new(b"webhook-secret", raw_body, hashlib.sha256).hexdigest()
    assert verify_webhook_signature(raw_body, signature)
    assert not verify_webhook_signature(raw_body + b" ", signature)


def test_recompute_premium_stacks_early_renewals() -> None:
    first_payment = datetime(2026, 1, 1, tzinfo=UTC)
    second_payment = datetime(2026, 6, 1, tzinfo=UTC)
    grants = [
        SimpleNamespace(id=1, granted_at=first_payment, duration_days=365),
        SimpleNamespace(id=2, granted_at=second_payment, duration_days=365),
    ]
    user = User(id=7, email="paid@example.com", password_hash="not-used")

    recompute_premium(_GrantSession(grants), user, now=first_payment)  # type: ignore[arg-type]

    assert user.premium_activated_at == first_payment
    assert user.premium_until == first_payment + timedelta(days=730)
    assert user.is_premium is True


def test_recompute_premium_revokes_access_without_grants() -> None:
    user = User(
        id=8,
        email="refunded@example.com",
        password_hash="not-used",
        is_premium=True,
        premium_until=datetime(2030, 1, 1, tzinfo=UTC),
    )

    recompute_premium(_GrantSession([]), user)  # type: ignore[arg-type]

    assert user.premium_activated_at is None
    assert user.premium_until is None
    assert user.is_premium is False


def test_production_rejects_debug_and_dev_unlock() -> None:
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            environment="production",
            debug=True,
            allow_dev_premium_unlock=True,
            secret_key="secure-production-secret",
        )


def test_partial_razorpay_credentials_are_rejected() -> None:
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            razorpay_key_id="rzp_test_example",
            razorpay_key_secret="",
        )


def test_production_payments_require_webhook_secret() -> None:
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            environment="production",
            secret_key="secure-production-secret",
            razorpay_key_id="rzp_live_example",
            razorpay_key_secret="api-secret",
            razorpay_webhook_secret="",
        )
