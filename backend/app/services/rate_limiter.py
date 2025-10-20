from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Deque, Dict, Optional

try:
    from redis import Redis  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    Redis = None

from fastapi import HTTPException, status


class RateLimiter:
    def __init__(
        self,
        requests: int,
        window_seconds: int,
        *,
        redis_client: Optional["Redis"] = None,
        prefix: str = "ratelimit",
    ) -> None:
        self.requests = requests
        self.window_seconds = window_seconds
        self._hits: Dict[str, Deque[float]] = defaultdict(deque)
        self._redis = redis_client if Redis is not None else None
        self._prefix = prefix

    def check(self, key: str) -> None:
        if self._redis is not None:
            self._check_redis(key)
            return
        self._check_memory(key)

    def _check_memory(self, key: str) -> None:
        now = time.time()
        window_start = now - self.window_seconds
        queue = self._hits[key]
        while queue and queue[0] < window_start:
            queue.popleft()
        if len(queue) >= self.requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please retry later.",
            )
        queue.append(now)

    def _check_redis(self, key: str) -> None:
        assert self._redis is not None  # for type checkers
        now_ms = int(time.time() * 1000)
        window_start = now_ms - int(self.window_seconds * 1000)
        redis_key = f"{self._prefix}:{key}"
        try:
            pipeline = self._redis.pipeline()
            pipeline.zadd(redis_key, {str(now_ms): now_ms})
            pipeline.zremrangebyscore(redis_key, 0, window_start)
            pipeline.zcard(redis_key)
            pipeline.expire(redis_key, self.window_seconds)
            _, _, count, _ = pipeline.execute()
        except Exception:  # pragma: no cover - failsafe fallback
            self._check_memory(key)
            return
        if count > self.requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please retry later.",
            )


__all__ = ["RateLimiter"]
