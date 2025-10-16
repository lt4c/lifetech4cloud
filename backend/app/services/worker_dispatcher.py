from __future__ import annotations

import asyncio
from typing import Any, Dict
from uuid import UUID

import httpx

from app.models import VpsProduct, VpsSession, Worker
from app.settings import get_settings


class WorkerDispatcher:
    def __init__(self) -> None:
        timeout = httpx.Timeout(10.0, connect=5.0)
        self._client = httpx.AsyncClient(timeout=timeout)
        self._lock = asyncio.Lock()
        self._settings = get_settings()

    async def aclose(self) -> None:
        await self._client.aclose()

    async def dispatch_job(
        self,
        *,
        worker: Worker,
        session: VpsSession,
        product: VpsProduct,
        session_token: str,
        callback_base: str,
        auth_token: str,
        extra: Dict[str, Any] | None = None,
    ) -> httpx.Response:
        payload: Dict[str, Any] = {
            "worker_id": str(worker.id),
            "session_id": str(session.id),
            "session_token": session_token,
            "product": {
                "id": str(product.id) if product.id else None,
                "name": product.name,
                "price_coins": product.price_coins,
                "description": product.description,
            },
            "callback_urls": {
                "status": f"{callback_base}/workers/callback/status",
                "checklist": f"{callback_base}/workers/callback/checklist",
                "result": f"{callback_base}/workers/callback/result",
            },
        }
        if extra:
            payload.update(extra)
        url = worker.base_url.rstrip("/") + "/job/create"
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        }
        async with self._lock:
            response = await self._client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response


__all__ = ["WorkerDispatcher"]
