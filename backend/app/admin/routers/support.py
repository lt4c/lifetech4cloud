from __future__ import annotations

import asyncio
import json
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.admin.audit import AuditContext
from app.admin.deps import require_perm
from app.admin.schemas import (
    SupportMessageDTO,
    SupportReplyRequest,
    SupportThreadDetail,
    SupportThreadSummary,
)
from app.deps import get_db, get_support_bus
from app.models import SupportMessage, SupportThread, User
from app.services.support import SupportService
from app.services.support_event_bus import SupportEventBus


router = APIRouter(tags=["admin-support"])


def _audit_context(request: Request, actor: User) -> AuditContext:
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    return AuditContext(actor_user_id=actor.id, ip=ip, ua=ua)


def _message_dto(message: SupportMessage) -> SupportMessageDTO:
    attachments = [
        {
            "url": item["url"],
            "label": item.get("label"),
            "kind": item.get("kind"),
        }
        for item in SupportService.attachments_for_message(message)
    ]
    return SupportMessageDTO(
        id=message.id,
        sender=message.sender,
        content=message.content,
        role=message.role,
        meta=message.meta,
        attachments=attachments,
        created_at=message.created_at,
    )


def _summary(thread: SupportThread) -> SupportThreadSummary:
    messages = thread.messages or []
    last_message = messages[-1] if messages else None
    return SupportThreadSummary(
        id=thread.id,
        user_id=thread.user_id,
        source=thread.source,
        status=thread.status,
        created_at=thread.created_at,
        updated_at=thread.updated_at,
        last_message_at=last_message.created_at if last_message else thread.updated_at,
    )


def _detail(thread: SupportThread, messages: List[SupportMessage]) -> SupportThreadDetail:
    return SupportThreadDetail(
        id=thread.id,
        user_id=thread.user_id,
        source=thread.source,
        status=thread.status,
        created_at=thread.created_at,
        updated_at=thread.updated_at,
        last_message_at=messages[-1].created_at if messages else thread.updated_at,
        messages=[_message_dto(msg) for msg in messages],
    )


@router.get("/support/threads", response_model=list[SupportThreadSummary])
async def list_threads(
    status_filter: str | None = Query(None, alias="status"),
    _: User = Depends(require_perm("support:threads:read")),
    db: Session = Depends(get_db),
) -> list[SupportThreadSummary]:
    service = SupportService(db)
    threads = service.list_threads(status_filter=status_filter)
    return [_summary(thread) for thread in threads]


@router.get("/support/threads/{thread_id}", response_model=SupportThreadDetail)
async def get_thread(
    thread_id: UUID,
    _: User = Depends(require_perm("support:threads:read")),
    db: Session = Depends(get_db),
) -> SupportThreadDetail:
    service = SupportService(db)
    thread = service.get_thread(thread_id)
    messages = service.thread_messages(thread)
    return _detail(thread, messages)


@router.post("/support/threads/{thread_id}/reply", response_model=SupportThreadDetail)
async def reply_thread(
    request: Request,
    thread_id: UUID,
    payload: SupportReplyRequest,
    actor: User = Depends(require_perm("support:threads:reply")),
    db: Session = Depends(get_db),
    support_bus: SupportEventBus = Depends(get_support_bus),
) -> SupportThreadDetail:
    service = SupportService(db)
    thread = service.get_thread(thread_id)
    context = _audit_context(request, actor)
    raw_attachments = [item.model_dump() for item in (payload.attachments or [])]
    attachments = SupportService.normalize_attachments(raw_attachments)
    reply = service.admin_reply(
        thread=thread,
        message=payload.message,
        status_value=payload.status,
        attachments=attachments,
    )
    await support_bus.publish(
        thread.id,
        {"event": "message.created", "data": SupportService.message_payload(reply)},
    )
    await support_bus.publish(
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
    messages = service.thread_messages(thread)
    return _detail(thread, messages)


@router.get("/support/threads/{thread_id}/events")
async def admin_thread_events(
    thread_id: UUID,
    request: Request,
    _: User = Depends(require_perm("support:threads:read")),
    db: Session = Depends(get_db),
    support_bus: SupportEventBus = Depends(get_support_bus),
) -> StreamingResponse:
    service = SupportService(db)
    thread = service.get_thread(thread_id)
    messages = service.thread_messages(thread)
    initial_payload = SupportService.thread_payload(thread, messages)

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


def _format_sse(event: str, payload: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(payload)}\n\n"

