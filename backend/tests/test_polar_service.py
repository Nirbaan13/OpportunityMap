import base64
import hashlib
import hmac

from app.config import settings
from app.services.polar_service import verify_webhook_signature


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
