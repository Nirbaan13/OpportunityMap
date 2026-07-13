"""Fetch pages with curl_cffi (TLS fingerprinting — works on sites that block plain requests)."""

from __future__ import annotations

import logging
import time

from curl_cffi import requests

logger = logging.getLogger(__name__)

DEFAULT_IMPERSONATE = "chrome131"


class CurlClient:
    def __init__(self, *, delay_seconds: float = 1.0, impersonate: str = DEFAULT_IMPERSONATE) -> None:
        self.delay_seconds = delay_seconds
        self.impersonate = impersonate
        self._session = requests.Session()

    def __enter__(self) -> "CurlClient":
        return self

    def __exit__(self, *args: object) -> None:
        self._session.close()

    def fetch_html(self, url: str) -> str:
        response = self._session.get(url, impersonate=self.impersonate, timeout=60)
        response.raise_for_status()
        logger.debug("Fetched %s (%s bytes, status=%s)", url, len(response.text), response.status_code)
        if self.delay_seconds > 0:
            time.sleep(self.delay_seconds)
        return response.text

    def fetch_json(self, url: str, *, params: dict | None = None) -> dict:
        response = self._session.get(
            url,
            params=params,
            impersonate=self.impersonate,
            timeout=60,
            headers={"Accept": "application/json"},
        )
        response.raise_for_status()
        logger.debug("Fetched JSON %s (status=%s)", url, response.status_code)
        if self.delay_seconds > 0:
            time.sleep(self.delay_seconds)
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError(f"Expected JSON object from {url}")
        return payload
