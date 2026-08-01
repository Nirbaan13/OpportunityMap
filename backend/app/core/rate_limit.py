"""Best-effort in-process rate limiting for auth/admin abuse.

Works within a single serverless/worker instance. Not a cluster-wide store —
still blocks naive bursts and credential stuffing against one cold start.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status

_lock = threading.Lock()
_hits: dict[str, deque[float]] = defaultdict(deque)


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        # First hop is the original client on Vercel / most proxies.
        return forwarded.split(",")[0].strip() or "unknown"
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def check_rate_limit(
    *,
    key: str,
    limit: int,
    window_seconds: int,
) -> None:
    """Raise 429 if ``key`` has exceeded ``limit`` hits in ``window_seconds``."""
    now = time.monotonic()
    cutoff = now - window_seconds
    with _lock:
        bucket = _hits[key]
        while bucket and bucket[0] < cutoff:
            bucket.popleft()
        if len(bucket) >= limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please wait a minute and try again.",
                headers={"Retry-After": str(window_seconds)},
            )
        bucket.append(now)


def rate_limit_dependency(*, scope: str, limit: int, window_seconds: int = 60):
    """FastAPI dependency factory: limit requests per client IP per scope."""

    def _dependency(request: Request) -> None:
        ip = client_ip(request)
        check_rate_limit(
            key=f"{scope}:{ip}",
            limit=limit,
            window_seconds=window_seconds,
        )

    return _dependency


# Clear buckets in tests without restarting the process.
def reset_rate_limits_for_tests() -> None:
    with _lock:
        _hits.clear()
