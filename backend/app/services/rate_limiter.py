from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Deque, Dict

from fastapi import HTTPException, status


class RateLimiter:
    def __init__(self, requests: int, window_seconds: int) -> None:
        self.requests = requests
        self.window_seconds = window_seconds
        self._hits: Dict[str, Deque[float]] = defaultdict(deque)

    def check(self, key: str) -> None:
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


__all__ = ["RateLimiter"]
