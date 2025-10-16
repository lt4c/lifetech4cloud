from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any, Dict, Set
from uuid import UUID


class SupportEventBus:
    """In-memory pub/sub for support thread events."""

    def __init__(self) -> None:
        self._subscribers: Dict[UUID, Set[asyncio.Queue]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def publish(self, thread_id: UUID, event: Dict[str, Any]) -> None:
        async with self._lock:
            queues = list(self._subscribers.get(thread_id, set()))
        if not queues:
            return
        for queue in queues:
            payload = event.copy()
            try:
                queue.put_nowait(payload)
            except asyncio.QueueFull:
                try:
                    queue.get_nowait()
                    queue.put_nowait(payload)
                except Exception:
                    continue

    async def subscribe(self, thread_id: UUID, *, max_queue_items: int = 100) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_items)
        async with self._lock:
            self._subscribers[thread_id].add(queue)
        return queue

    async def unsubscribe(self, thread_id: UUID, queue: asyncio.Queue) -> None:
        async with self._lock:
            subscribers = self._subscribers.get(thread_id)
            if not subscribers:
                return
            subscribers.discard(queue)
            if not subscribers:
                self._subscribers.pop(thread_id, None)
            while not queue.empty():
                queue.get_nowait()


__all__ = ["SupportEventBus"]
