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
    ) -> SupportMessage:
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
    ) -> SupportMessage:
        self.set_thread_status(thread, status_value)
        reply = self.add_message(thread=thread, sender="admin", content=message, role="assistant")
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
