from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse

from sqlalchemy.orm import Session

from app.deps import get_current_user, get_db, get_kyaro_assistant
from app.models import SupportMessage, SupportThread, User
from app.services.kyaro import KyaroAssistant
from app.services.rate_limiter import RateLimiter
from app.services.settings_store import SettingsStore
from app.services.support import SupportService

router = APIRouter(prefix="/support", tags=["support"])

_support_rate_limiter = RateLimiter(requests=10, window_seconds=60)


def _thread_payload(thread: SupportThread, messages: list[SupportMessage]) -> Dict[str, Any]:
    return {
        "id": str(thread.id),
        "source": thread.source,
        "status": thread.status,
        "created_at": thread.created_at.isoformat() if thread.created_at else None,
        "updated_at": thread.updated_at.isoformat() if thread.updated_at else None,
        "messages": [
            {
                "id": str(msg.id),
                "sender": msg.sender,
                "role": msg.role,
                "content": msg.content,
                "meta": msg.meta,
                "created_at": msg.created_at.isoformat() if msg.created_at else None,
            }
            for msg in messages
        ],
    }


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
        payload.append(_thread_payload(thread, list(messages)))
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
    return JSONResponse(_thread_payload(thread, list(messages)))


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
) -> JSONResponse:
    message = str(payload.get("message", "")).strip()
    if not message:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message is required")
    _ensure_rate_limit(user, "ai")
    service = SupportService(db)
    thread_identifier = payload.get("thread_id")
    new_thread_requested = bool(payload.get("new_thread"))
    thread = None
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

    service.add_message(thread=thread, sender="user", content=message, role="user")
    db.commit()

    history = service.thread_messages(thread)
    prompt = _kyaro_prompt(db)
    reply_text = await assistant.generate_reply(system_prompt=prompt, history=list(history))
    service.add_message(thread=thread, sender="ai", content=reply_text, role="assistant")
    service.set_thread_status(thread, "open")
    db.commit()

    messages = service.thread_messages(thread)
    return JSONResponse(_thread_payload(thread, list(messages)))


@router.post("/threads", status_code=status.HTTP_201_CREATED)
async def create_human_thread(
    payload: Dict[str, Any],
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JSONResponse:
    message = str(payload.get("message", "")).strip()
    if not message:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message is required")
    _ensure_rate_limit(user, "human")
    service = SupportService(db)
    thread = service.create_thread(user=user, source="human")
    service.add_message(thread=thread, sender="user", content=message, role="user")
    db.commit()
    messages = service.thread_messages(thread)
    return JSONResponse(_thread_payload(thread, list(messages)))


@router.post("/threads/{thread_id}/message")
async def post_thread_message(
    thread_id: UUID,
    payload: Dict[str, Any],
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JSONResponse:
    message = str(payload.get("message", "")).strip()
    if not message:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message is required")
    _ensure_rate_limit(user, "human")
    service = SupportService(db)
    thread = service.get_thread_for_user(thread_id, user.id)
    if thread.source != "human":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Thread does not accept manual replies")
    service.add_message(thread=thread, sender="user", content=message, role="user")
    service.set_thread_status(thread, "pending")
    db.commit()
    messages = service.thread_messages(thread)
    return JSONResponse(_thread_payload(thread, list(messages)))
