from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, Iterable, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse, StreamingResponse

from sqlalchemy.orm import Session

from app.deps import get_current_user, get_db, get_kyaro_assistant, get_support_bus
from app.models import SupportMessage, SupportThread, User
from app.services.kyaro import KyaroAssistant
from app.services.rate_limiter import RateLimiter
from app.services.settings_store import SettingsStore
from app.services.support import SupportService
from app.services.support_event_bus import SupportEventBus

router = APIRouter(prefix="/support", tags=["support"])

_support_rate_limiter = RateLimiter(requests=10, window_seconds=60)


def _message_payload(message: SupportMessage) -> Dict[str, Any]:
    return SupportService.message_payload(message)


def _thread_payload(thread: SupportThread, messages: Iterable[SupportMessage]) -> Dict[str, Any]:
    return SupportService.thread_payload(thread, list(messages))


def _normalize_attachments(raw: Any) -> list[dict]:
    data = raw
    if isinstance(raw, str):
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = []
    if isinstance(data, list):
        return SupportService.normalize_attachments(data)
    return []


def _format_sse(event: str, payload: Dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(payload)}\n\n"


async def _publish_message_event(bus: SupportEventBus, thread_id: UUID, message: SupportMessage) -> None:
    await bus.publish(
        thread_id,
        {
            "event": "message.created",
            "data": _message_payload(message),
        },
    )


async def _publish_status_event(bus: SupportEventBus, thread: SupportThread) -> None:
    await bus.publish(
        thread.id,
        {
            "event": "thread.status",
            "data": {
                "thread_id": str(thread.id),
                "status": thread.status,
                "updated_at": thread.updated_at.isoformat() if thread.updated_at else None,
            },
        },
    )


@router.get("/threads")
async def list_threads(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JSONResponse:
    service = SupportService(db)
    threads = service.list_threads_for_user(user.id)
    payload = []
    for thread in threads:
        messages = service.thread_messages(thread)
        payload.append(_thread_payload(thread, messages))
    return JSONResponse({"threads": payload})


@router.get("/threads/{thread_id}")
async def get_thread(
    thread_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JSONResponse:
    service = SupportService(db)
    thread = service.get_thread_for_user(thread_id, user.id)
    messages = service.thread_messages(thread)
    return JSONResponse(_thread_payload(thread, messages))


def _ensure_rate_limit(user: User, scope: str) -> None:
    key = f"support:{scope}:{user.id}"
    _support_rate_limiter.check(key)


def _kyaro_prompt(db: Session) -> str:
    store = SettingsStore(db)
    record = store.get("kyaro.system_prompt", default={"prompt": ""})
    prompt = record.get("prompt") or ""
    return str(prompt)


@router.post("/ask")
async def ask_kyaro(
    payload: Dict[str, Any],
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    assistant: KyaroAssistant = Depends(get_kyaro_assistant),
    support_bus: SupportEventBus = Depends(get_support_bus),
) -> JSONResponse:
    message = str(payload.get("message", "")).strip()
    if not message:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message is required")
    _ensure_rate_limit(user, "ai")
    service = SupportService(db)
    thread_identifier = payload.get("thread_id")
    new_thread_requested = bool(payload.get("new_thread"))
    thread = None
    attachments = _normalize_attachments(payload.get("attachments"))
    if thread_identifier:
        try:
            thread_id = UUID(str(thread_identifier))
        except (TypeError, ValueError):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid thread identifier")
        thread = service.get_thread_for_user(thread_id, user.id)
        if thread.source != "ai":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Thread does not accept AI responses")
    elif new_thread_requested:
        thread = service.create_thread(user=user, source="ai")
    else:
        thread = service.ensure_thread(user=user, source="ai")

    user_message = service.add_message(thread=thread, sender="user", content=message, role="user", attachments=attachments)
    db.commit()
    await _publish_message_event(support_bus, thread.id, user_message)

    history = service.thread_messages(thread)
    prompt = _kyaro_prompt(db)
    reply_text = await assistant.generate_reply(system_prompt=prompt, history=list(history))
    ai_message = service.add_message(thread=thread, sender="ai", content=reply_text, role="assistant")
    service.set_thread_status(thread, "open")
    db.commit()
    await _publish_message_event(support_bus, thread.id, ai_message)
    await _publish_status_event(support_bus, thread)

    messages = service.thread_messages(thread)
    return JSONResponse(_thread_payload(thread, messages))


@router.post("/threads", status_code=status.HTTP_201_CREATED)
async def create_human_thread(
    payload: Dict[str, Any],
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    support_bus: SupportEventBus = Depends(get_support_bus),
) -> JSONResponse:
    message = str(payload.get("message", "")).strip()
    if not message:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message is required")
    _ensure_rate_limit(user, "human")
    service = SupportService(db)
    thread = service.create_thread(user=user, source="human")
    attachments = _normalize_attachments(payload.get("attachments"))
    new_message = service.add_message(thread=thread, sender="user", content=message, role="user", attachments=attachments)
    db.commit()
    await _publish_message_event(support_bus, thread.id, new_message)
    await _publish_status_event(support_bus, thread)
    messages = service.thread_messages(thread)
    return JSONResponse(_thread_payload(thread, messages))


@router.post("/threads/{thread_id}/message")
async def post_thread_message(
    thread_id: UUID,
    payload: Dict[str, Any],
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    support_bus: SupportEventBus = Depends(get_support_bus),
) -> JSONResponse:
    message = str(payload.get("message", "")).strip()
    if not message:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message is required")
    _ensure_rate_limit(user, "human")
    service = SupportService(db)
    thread = service.get_thread_for_user(thread_id, user.id)
    if thread.source != "human":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Thread does not accept manual replies")
    attachments = _normalize_attachments(payload.get("attachments"))
    new_message = service.add_message(thread=thread, sender="user", content=message, role="user", attachments=attachments)
    service.set_thread_status(thread, "pending")
    db.commit()
    await _publish_message_event(support_bus, thread.id, new_message)
    await _publish_status_event(support_bus, thread)
    messages = service.thread_messages(thread)
    return JSONResponse(_thread_payload(thread, messages))


@router.get("/threads/{thread_id}/events")
async def stream_thread_events(
    thread_id: UUID,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    support_bus: SupportEventBus = Depends(get_support_bus),
) -> StreamingResponse:
    service = SupportService(db)
    thread = service.get_thread_for_user(thread_id, user.id)
    messages = service.thread_messages(thread)
    initial_payload = _thread_payload(thread, messages)

    queue = await support_bus.subscribe(thread.id)

    async def event_generator():
        try:
            yield _format_sse("thread.snapshot", initial_payload)
            while True:
                try:
                    item = await asyncio.wait_for(queue.get(), timeout=25)
                except asyncio.TimeoutError:
                    yield ": ping\n\n"
                    continue
                event_type = item.get("event", "message")
                data = item.get("data", {})
                yield _format_sse(event_type, data)
        finally:
            await support_bus.unsubscribe(thread.id, queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
