# academic-advisor/academic-advisor-backend/app/api/middleware/rate_limit.py
"""
Rate limiting middleware  (Task 21)
Uses in-memory store (no Redis dependency required)
"""

import time
import logging
from collections import defaultdict
from typing import Dict, Tuple
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.constants import RATE_LIMITS

logger = logging.getLogger(__name__)


class _TokenBucket:
    """Simple per-key token bucket"""

    def __init__(self):
        self._buckets: Dict[str, Tuple[float, float]] = {}  # key → (tokens, last_refill)

    def allow(self, key: str, max_tokens: int, refill_period: float) -> bool:
        now = time.time()
        tokens, last = self._buckets.get(key, (float(max_tokens), now))

        elapsed = now - last
        tokens = min(max_tokens, tokens + elapsed * (max_tokens / refill_period))

        if tokens >= 1:
            self._buckets[key] = (tokens - 1, now)
            return True

        self._buckets[key] = (tokens, now)
        return False

    def cleanup(self, max_age: float = 600):
        now = time.time()
        stale = [k for k, (_, t) in self._buckets.items() if now - t > max_age]
        for k in stale:
            del self._buckets[k]


_bucket = _TokenBucket()
_cleanup_counter = 0


class RateLimitMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        global _cleanup_counter

        # Determine rate limit config
        path = request.url.path.lower()
        if "/auth" in path:
            cfg = RATE_LIMITS["AUTH"]
        elif "/upload" in path or "/cv" in path:
            cfg = RATE_LIMITS["UPLOAD"]
        elif "/export" in path:
            cfg = RATE_LIMITS["EXPORT"]
        else:
            cfg = RATE_LIMITS["DEFAULT"]

        # Key = IP + optional user
        ip = request.client.host if request.client else "unknown"
        user_id = ""
        if hasattr(request.state, "user") and request.state.user:
            user_id = request.state.user.get("uid", "")
        key = f"rl:{ip}:{user_id}:{path.split('/')[3] if len(path.split('/')) > 3 else 'root'}"

        if not _bucket.allow(key, cfg["requests"], cfg["period"]):
            logger.warning(f"Rate limit hit: {key}")
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please slow down."},
            )

        # Periodic cleanup
        _cleanup_counter += 1
        if _cleanup_counter % 500 == 0:
            _bucket.cleanup()

        return await call_next(request)