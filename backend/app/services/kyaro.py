from __future__ import annotations

import asyncio
from typing import Iterable, Sequence

from fastapi import HTTPException, status
from openai import AsyncOpenAI

from app.models import SupportMessage
from app.settings import get_settings

def _sanitize(text: str | None) -> str:
    if not text:
        return ""
    lowered = text.lower()
    if "session" in lowered or "token" in lowered:
        return "[chung toi chua ho tro hien thi tinh nang nay]"
    return text


class KyaroAssistant:
    def __init__(self) -> None:
        self._client: AsyncOpenAI | None = None
        self._lock = asyncio.Lock()
        self._settings = get_settings()

    async def _get_client(self) -> AsyncOpenAI:
        async with self._lock:
            if self._client is None:
                base_url = self._settings.hface_gpt_base_url
                if not base_url:
                    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Kyaro AI unavailable")
                api_key = self._settings.openai_api_key or "hf-placeholder-key"
                self._client = AsyncOpenAI(api_key=api_key, base_url=str(base_url))
            return self._client

    async def generate_reply(self, *, system_prompt: str, history: Sequence[SupportMessage]) -> str:
        client = await self._get_client()
        messages = [{"role": "system", "content": system_prompt}]
        for item in history:
            role = item.role or ("assistant" if item.sender in {"ai", "admin"} else "user")
            messages.append({"role": role, "content": _sanitize(item.content)})
        try:
            response = await client.chat.completions.create(
                model=self._settings.hface_gpt_model,
                messages=messages,
                temperature=0.4,
                max_tokens=1024,
            )
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Kyaro AI error") from exc
        choice = response.choices[0]
        content = choice.message.content or ""
        return _sanitize(content)


__all__ = ["KyaroAssistant"]
