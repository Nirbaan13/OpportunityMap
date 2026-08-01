import base64
import hashlib
import hmac
import io
from unittest.mock import MagicMock

import pytest
import urllib.error
from fastapi import HTTPException

from app.config import settings
from app.services.polar_service import (
    _POLAR_USER_AGENT,
    _checkout_belongs_to_user,
    _checkout_success_url,
    _format_polar_error_body,
    _map_checkout_status,
    _polar_request,
    _require_polar_product_id,
    create_checkout,
    reconcile_checkout,
    verify_webhook_signature,
)


def test_polar_webhook_signature(monkeypatch) -> None:
    secret = base64.b64encode(b"polar-test-secret").decode()
    monkeypatch.setattr(settings, "polar_webhook_secret", secret)
    body = b'{"type":"order.paid","data":{"id":"ord_1"}}'
    webhook_id = "msg_123"
    timestamp = "1710000000"
    signed = f"{webhook_id}.{timestamp}.{body.decode()}".encode()
    digest = hmac.new(base64.b64decode(secret), signed, hashlib.sha256).digest()
    signature = "v1," + base64.b64encode(digest).decode()

    assert verify_webhook_signature(
        raw_body=body,
        webhook_id=webhook_id,
        webhook_timestamp=timestamp,
        webhook_signature=signature,
    )
    assert not verify_webhook_signature(
        raw_body=body + b" ",
        webhook_id=webhook_id,
        webhook_timestamp=timestamp,
        webhook_signature=signature,
    )


def test_format_polar_error_body_detail_string() -> None:
    raw = b'{"detail":"Product does not exist"}'
    assert "Product does not exist" in _format_polar_error_body(raw, 422)


def test_format_polar_error_body_validation_list() -> None:
    raw = (
        b'{"detail":[{"loc":["body","products",0],"msg":"Input should be a valid UUID",'
        b'"type":"uuid_parsing"}]}'
    )
    msg = _format_polar_error_body(raw, 422)
    assert "valid UUID" in msg
    assert "products" in msg


def test_format_polar_error_body_cloudflare_browser_signature() -> None:
    raw = (
        b"The site owner has blocked access based on your browser's "
        b"signature (error code: 1010)."
    )
    msg = _format_polar_error_body(raw, 403)
    assert "network protection" in msg
    assert "browser's signature" not in msg.lower()
    assert "1010" not in msg


def test_format_polar_error_body_html_non_json() -> None:
    raw = b"<!DOCTYPE html><html><body>Cloudflare</body></html>"
    msg = _format_polar_error_body(raw, 403)
    assert "network protection" in msg
    assert "<html" not in msg.lower()


def test_polar_request_sets_user_agent(monkeypatch) -> None:
    monkeypatch.setattr(settings, "polar_access_token", "tok")
    monkeypatch.setattr(settings, "polar_api_base", "https://api.polar.sh/v1")

    captured: dict = {}

    class _Resp:
        def read(self) -> bytes:
            return b'{"ok":true}'

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    def fake_urlopen(req, timeout=30):
        captured["headers"] = dict(req.header_items())
        captured["url"] = req.full_url
        return _Resp()

    monkeypatch.setattr(
        "app.services.polar_service.urllib.request.urlopen",
        fake_urlopen,
    )
    assert _polar_request("GET", "/products/") == {"ok": True}
    headers = {k.lower(): v for k, v in captured["headers"].items()}
    assert headers["user-agent"] == _POLAR_USER_AGENT
    assert headers["authorization"] == "Bearer tok"
    assert headers["accept"] == "application/json"
    assert "Python-urllib" not in headers["user-agent"]
    assert captured["url"] == "https://api.polar.sh/v1/products/"


def test_require_polar_product_id_rejects_non_uuid(monkeypatch) -> None:
    monkeypatch.setattr(settings, "polar_product_id", "not-a-uuid")
    with pytest.raises(HTTPException) as exc:
        _require_polar_product_id()
    assert exc.value.status_code == 503
    assert "UUID" in str(exc.value.detail)


def test_checkout_success_url_requires_absolute(monkeypatch) -> None:
    monkeypatch.setattr(settings, "frontend_url", "opportunitymap.info")
    with pytest.raises(HTTPException) as exc:
        _checkout_success_url()
    assert exc.value.status_code == 503


def test_create_checkout_surfaces_polar_http_error(monkeypatch) -> None:
    monkeypatch.setattr(settings, "polar_access_token", "tok")
    monkeypatch.setattr(
        settings, "polar_product_id", "11111111-1111-1111-1111-111111111111"
    )
    monkeypatch.setattr(settings, "frontend_url", "https://opportunitymap.info")

    fp = io.BytesIO(b'{"detail":"Product is not available"}')
    err = urllib.error.HTTPError(
        "https://api.polar.sh/v1/checkouts/",
        422,
        "Unprocessable",
        hdrs=None,  # type: ignore[arg-type]
        fp=fp,
    )
    monkeypatch.setattr(
        "app.services.polar_service.urllib.request.urlopen",
        MagicMock(side_effect=err),
    )

    user = MagicMock()
    user.id = 7
    user.email = "student@example.com"
    user.profile = MagicMock(country_code="NL")
    db = MagicMock()

    with pytest.raises(HTTPException) as exc:
        create_checkout(db, user)
    assert exc.value.status_code == 502
    assert "Product is not available" in str(exc.value.detail)


def test_checkout_belongs_to_user_via_metadata() -> None:
    user = MagicMock()
    user.id = 7
    user.email = "student@example.com"
    assert _checkout_belongs_to_user({"metadata": {"user_id": "7"}}, user)
    assert not _checkout_belongs_to_user({"metadata": {"user_id": "9"}}, user)
    assert _checkout_belongs_to_user({"external_customer_id": "7"}, user)
    assert _checkout_belongs_to_user({"customer_email": "Student@Example.com"}, user)
    assert not _checkout_belongs_to_user({}, user)


def test_map_checkout_status() -> None:
    assert _map_checkout_status("open", is_premium=False) == "created"
    assert _map_checkout_status("confirmed", is_premium=False) == "created"
    assert _map_checkout_status("confirmed", is_premium=True) == "paid"
    assert _map_checkout_status("failed", is_premium=False) == "failed"
    assert _map_checkout_status("expired", is_premium=False) == "failed"


def test_reconcile_checkout_grants_from_confirmed_order(monkeypatch) -> None:
    monkeypatch.setattr(settings, "polar_access_token", "tok")
    monkeypatch.setattr(
        settings, "polar_product_id", "11111111-1111-1111-1111-111111111111"
    )

    checkout_id = "22222222-2222-2222-2222-222222222222"
    order = {
        "id": "ord_paid_1",
        "billing_reason": "subscription_create",
        "metadata": {"user_id": "7"},
    }

    def fake_polar(method: str, path: str, payload=None):
        assert method == "GET"
        if path == f"/checkouts/{checkout_id}":
            return {
                "id": checkout_id,
                "status": "confirmed",
                "metadata": {"user_id": "7"},
                "external_customer_id": "7",
                "order": order,
            }
        raise AssertionError(f"unexpected path {path}")

    applied: list[dict] = []

    def fake_apply(db, entity):
        applied.append(entity)

    monkeypatch.setattr(
        "app.services.polar_service._polar_request", fake_polar
    )
    monkeypatch.setattr(
        "app.services.polar_service._apply_paid_order", fake_apply
    )

    user = MagicMock()
    user.id = 7
    user.email = "student@example.com"
    user.premium_until = None
    db = MagicMock()

    from datetime import UTC, datetime, timedelta

    user.premium_until = datetime.now(UTC) + timedelta(days=365)

    result = reconcile_checkout(db, user, checkout_id)
    assert applied and applied[0]["id"] == "ord_paid_1"
    assert result["order_id"] == checkout_id
    assert result["status"] == "paid"
    assert result["is_premium"] is True
    db.commit.assert_called_once()


def test_reconcile_checkout_rejects_other_users_checkout(monkeypatch) -> None:
    monkeypatch.setattr(settings, "polar_access_token", "tok")
    monkeypatch.setattr(
        settings, "polar_product_id", "11111111-1111-1111-1111-111111111111"
    )
    checkout_id = "22222222-2222-2222-2222-222222222222"

    monkeypatch.setattr(
        "app.services.polar_service._polar_request",
        lambda method, path, payload=None: {
            "id": checkout_id,
            "status": "confirmed",
            "metadata": {"user_id": "99"},
            "external_customer_id": "99",
        },
    )

    user = MagicMock()
    user.id = 7
    user.email = "student@example.com"
    db = MagicMock()

    with pytest.raises(HTTPException) as exc:
        reconcile_checkout(db, user, checkout_id)
    assert exc.value.status_code == 404
