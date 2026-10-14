from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from typing import Deque, Dict

from fastapi import HTTPException, Request

from app.core.config import settings

_WINDOW_SECONDS = 60
_hits: Dict[str, Deque[float]] = defaultdict(deque)
_lock = threading.Lock()


def _client_ip(request: Request) -> str:
    if settings.trust_proxy_headers:
        forwarded = request.headers.get("x-forwarded-for", "")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def rate_limit(request: Request) -> None:
    """FastAPI dependency: sliding window, in-memory (single worker)."""
    limit = settings.rate_limit_per_minute
    if limit <= 0:
        return
    ip = _client_ip(request)
    now = time.monotonic()
    with _lock:
        window = _hits[ip]
        while window and now - window[0] > _WINDOW_SECONDS:
            window.popleft()
        if len(window) >= limit:
            retry_after = int(_WINDOW_SECONDS - (now - window[0])) + 1
            raise HTTPException(
                status_code=429,
                detail="Bạn gửi quá nhiều câu hỏi. Vui lòng thử lại sau ít phút.",
                headers={"Retry-After": str(retry_after)},
            )
        window.append(now)
        if len(_hits) > 10_000:  # drop idle IPs so the dict cannot grow forever
            for key in [k for k, v in _hits.items() if not v or now - v[-1] > _WINDOW_SECONDS]:
                del _hits[key]
