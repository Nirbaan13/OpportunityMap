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
    _checkout_success_url,
    _format_polar_error_body,
    _require_polar_product_id,
    create_checkout,
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
