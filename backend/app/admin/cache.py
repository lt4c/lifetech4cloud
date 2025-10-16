from __future__ import annotations

import json
import time
from threading import RLock
from typing import Iterable
from uuid import UUID

try:
    import redis  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    redis = None

from .admin_settings import get_admin_settings


class PermissionCache:
    def __init__(self, ttl_seconds: int = 60) -> None:
        self._ttl = ttl_seconds
        self._memory_store: dict[UUID, tuple[float, set[str]]] = {}
        self._lock = RLock()
        self._redis = self._init_redis()

    @staticmethod
    def _init_redis():
        settings = get_admin_settings()
        if not settings.redis_url or not redis:
            return None
        try:
            client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
            client.ping()
            return client
        except Exception:  # pragma: no cover - best effort
            return None

    def get(self, user_id: UUID) -> set[str] | None:
        if self._redis is not None:
            payload = self._redis.get(self._redis_key(user_id))
            if payload is None:
                return None
            return set(json.loads(payload))

        with self._lock:
            cached = self._memory_store.get(user_id)
            if not cached:
                return None
            expires_at, values = cached
            if expires_at < time.time():
                self._memory_store.pop(user_id, None)
                return None
            return set(values)

    def set(self, user_id: UUID, permissions: Iterable[str]) -> None:
        values = list(permissions)
        if self._redis is not None:
            self._redis.setex(
                self._redis_key(user_id),
                self._ttl,
                json.dumps(sorted(values)),
            )
            return

        with self._lock:
            self._memory_store[user_id] = (time.time() + self._ttl, set(values))

    def invalidate(self, user_id: UUID) -> None:
        if self._redis is not None:
            self._redis.delete(self._redis_key(user_id))
            return
        with self._lock:
            self._memory_store.pop(user_id, None)

    @staticmethod
    def _redis_key(user_id: UUID) -> str:
        return f"admin:perms:{user_id}"


_permission_cache: PermissionCache | None = None


def get_permission_cache() -> PermissionCache:
    global _permission_cache
    if _permission_cache is None:
        settings = get_admin_settings()
        _permission_cache = PermissionCache(ttl_seconds=settings.rate_limit.window_seconds)
    return _permission_cache
