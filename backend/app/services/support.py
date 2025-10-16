from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable, List, Sequence
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import SupportMessage, SupportThread, User


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SupportService:
    def __init__(self, db: Session) -> None:
        self.db = db

    @staticmethod
    def normalize_attachments(raw: Iterable[dict] | None) -> list[dict]:
        attachments: list[dict] = []
        if not raw:
            return attachments
        for item in raw:
            if not isinstance(item, dict):
                continue
            url_value = str(item.get("url") or "").strip()
            if not url_value:
                continue
            label_value = str(item.get("label") or "").strip() or None
            kind_value = str(item.get("kind") or "").strip().lower()
            if kind_value not in {"link", "image", "file"}:
                kind_value = "image" if url_value.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")) else "link"
            attachments.append(
                {
                    "url": url_value,
                    "label": label_value,
                    "kind": kind_value,
                }
            )
        return attachments

    @staticmethod
    def attachments_for_message(message: SupportMessage) -> list[dict]:
        meta = message.meta or {}
        raw = meta.get("attachments")
        if isinstance(raw, list):
            return SupportService.normalize_attachments(raw)
        return []

    @staticmethod
    def message_payload(message: SupportMessage) -> dict:
        return {
            "id": str(message.id),
            "sender": message.sender,
            "role": message.role,
            "content": message.content,
            "attachments": SupportService.attachments_for_message(message),
            "meta": message.meta,
            "created_at": message.created_at.isoformat() if message.created_at else None,
            "thread_id": str(message.thread_id),
        }

    @staticmethod
    def thread_payload(thread: SupportThread, messages: Sequence[SupportMessage]) -> dict:
        return {
            "id": str(thread.id),
            "source": thread.source,
            "status": thread.status,
            "created_at": thread.created_at.isoformat() if thread.created_at else None,
            "updated_at": thread.updated_at.isoformat() if thread.updated_at else None,
            "messages": [SupportService.message_payload(msg) for msg in messages],
        }

    def _thread_query(self):
        return select(SupportThread).order_by(SupportThread.updated_at.desc())

    def list_threads(self, *, status_filter: str | None = None) -> List[SupportThread]:
        stmt = self._thread_query()
        if status_filter:
            stmt = stmt.where(SupportThread.status == status_filter)
        return list(self.db.scalars(stmt))

    def list_threads_for_user(self, user_id: UUID) -> List[SupportThread]:
        stmt = self._thread_query().where(SupportThread.user_id == user_id)
        return list(self.db.scalars(stmt))

    def get_thread(self, thread_id: UUID) -> SupportThread:
        thread = self.db.get(SupportThread, thread_id)
        if not thread:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Support thread not found")
        return thread

    def get_thread_for_user(self, thread_id: UUID, user_id: UUID) -> SupportThread:
        thread = self.get_thread(thread_id)
        if thread.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return thread

    def create_thread(self, *, user: User, source: str) -> SupportThread:
        now = _utcnow()
        thread = SupportThread(user_id=user.id, source=source, status="open", created_at=now, updated_at=now)
        self.db.add(thread)
        self.db.flush()
        return thread

    def ensure_thread(self, *, user: User, source: str = "ai") -> SupportThread:
        stmt = (
            select(SupportThread)
            .where(SupportThread.user_id == user.id)
            .where(SupportThread.source == source)
            .where(SupportThread.status.in_(["open", "pending"]))
            .order_by(SupportThread.updated_at.desc())
        )
        existing = self.db.scalars(stmt).first()
        if existing:
            return existing
        return self.create_thread(user=user, source=source)

    def set_thread_status(self, thread: SupportThread, status_value: str | None) -> None:
        if status_value and status_value != thread.status:
            thread.status = status_value

    def add_message(
        self,
        *,
        thread: SupportThread,
        sender: str,
        content: str | None,
        role: str | None = None,
        meta: dict | None = None,
        attachments: list[dict] | None = None,
    ) -> SupportMessage:
        meta = dict(meta or {})
        if attachments:
            meta["attachments"] = self.normalize_attachments(attachments)
        message = SupportMessage(
            thread_id=thread.id,
            sender=sender,
            content=content,
            role=role,
            meta=meta or {},
            created_at=_utcnow(),
        )
        thread.updated_at = message.created_at
        self.db.add(message)
        self.db.add(thread)
        self.db.flush()
        return message

    def admin_reply(
        self,
        *,
        thread: SupportThread,
        message: str,
        status_value: str | None,
        attachments: list[dict] | None = None,
    ) -> SupportMessage:
        self.set_thread_status(thread, status_value)
        reply = self.add_message(
            thread=thread,
            sender="admin",
            content=message,
            role="assistant",
            attachments=attachments,
        )
        self.db.commit()
        self.db.refresh(thread)
        return reply

    def close_thread(self, thread: SupportThread) -> None:
        if thread.status != "closed":
            thread.status = "closed"
            thread.updated_at = _utcnow()
            self.db.add(thread)
            self.db.commit()

    def thread_messages(self, thread: SupportThread) -> Sequence[SupportMessage]:
        stmt = select(SupportMessage).where(SupportMessage.thread_id == thread.id).order_by(SupportMessage.created_at.asc())
        return list(self.db.scalars(stmt))


__all__ = ["SupportService"]
