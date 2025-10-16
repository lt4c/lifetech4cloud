from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import urljoin
from uuid import UUID

import httpx
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.admin.audit import AuditContext, record_audit
from app.models import Worker, VpsSession

ACTIVE_STATUSES = {"pending", "provisioning", "ready"}


class WorkerRegistryService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _normalize_url(self, raw: str) -> str:
        url = raw.strip()
        if not url:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="base_url required")
        return url.rstrip("/")

    def _active_session_counts(self, worker_ids: list[UUID]) -> dict[UUID, int]:
        if not worker_ids:
            return {}
        stmt = (
            select(VpsSession.worker_id, func.count(VpsSession.id))
            .where(VpsSession.worker_id.in_(worker_ids))
            .where(VpsSession.status.in_(ACTIVE_STATUSES))
            .group_by(VpsSession.worker_id)
        )
        return {row[0]: row[1] for row in self.db.execute(stmt).all()}

    def list_workers(self) -> list[Worker]:
        stmt = select(Worker).order_by(Worker.created_at.desc())
        workers = list(self.db.scalars(stmt))
        counts = self._active_session_counts([worker.id for worker in workers])
        for worker in workers:
            setattr(worker, "_active_sessions", counts.get(worker.id, 0))
        return workers

    def get_worker(self, worker_id: UUID) -> Worker:
        worker = self.db.get(Worker, worker_id)
        if not worker:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found.")
        counts = self._active_session_counts([worker.id])
        setattr(worker, "_active_sessions", counts.get(worker.id, 0))
        return worker

    def register_worker(
        self,
        *,
        name: str | None,
        base_url: str,
        max_sessions: int,
        context: AuditContext,
    ) -> Worker:
        normalized_url = self._normalize_url(base_url)

        try:
            response = httpx.get(
                urljoin(normalized_url + "/", "health"),
                timeout=5.0,
                verify=False,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Worker health check failed: {exc}") from exc

        worker = Worker(
            name=name,
            base_url=normalized_url,
            status="active",
            max_sessions=max_sessions,
        )
        self.db.add(worker)
        self.db.commit()
        self.db.refresh(worker)
        setattr(worker, "_active_sessions", 0)

        record_audit(
            self.db,
            context=context,
            action="worker.register",
            target_type="worker",
            target_id=str(worker.id),
            before=None,
            after={
                "name": worker.name,
                "base_url": worker.base_url,
                "max_sessions": worker.max_sessions,
            },
        )
        self.db.commit()
        return worker

    def update_worker(
        self,
        worker_id: UUID,
        *,
        name: str | None = None,
        base_url: str | None = None,
        status: str | None = None,
        max_sessions: int | None = None,
        context: AuditContext,
    ) -> Worker:
        worker = self.db.get(Worker, worker_id)
        if not worker:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found.")
        before = {
            "name": worker.name,
            "base_url": worker.base_url,
            "status": worker.status,
            "max_sessions": worker.max_sessions,
        }
        if name is not None:
            worker.name = name
        if base_url is not None:
            worker.base_url = self._normalize_url(base_url)
        if status is not None:
            worker.status = status
        if max_sessions is not None:
            worker.max_sessions = max_sessions
        worker.updated_at = datetime.now(timezone.utc)
        self.db.add(worker)
        self.db.commit()
        self.db.refresh(worker)
        counts = self._active_session_counts([worker.id])
        setattr(worker, "_active_sessions", counts.get(worker.id, 0))
        after = {
            "name": worker.name,
            "base_url": worker.base_url,
            "status": worker.status,
            "max_sessions": worker.max_sessions,
        }
        record_audit(
            self.db,
            context=context,
            action="worker.update",
            target_type="worker",
            target_id=str(worker.id),
            before=before,
            after=after,
        )
        self.db.commit()
        return worker
