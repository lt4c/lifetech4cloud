from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.admin.audit import AuditContext, record_audit
from app.models import Setting


class SettingsStore:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _get_setting(self, key: str) -> Setting | None:
        stmt = select(Setting).where(Setting.key == key)
        return self.db.scalar(stmt)

    def get(self, key: str, default: dict | None = None) -> dict:
        entry = self._get_setting(key)
        if entry is None:
            if default is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Setting {key} not found")
            return default
        return dict(entry.value or {})

    def set(self, key: str, value: dict[str, Any], *, context: AuditContext) -> dict:
        entry = self._get_setting(key)
        before = dict(entry.value) if entry and entry.value else None
        if entry is None:
            entry = Setting(key=key, value=value)
            self.db.add(entry)
        else:
            entry.value = value
            entry.updated_at = datetime.now(timezone.utc)
            self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        record_audit(
            self.db,
            context=context,
            action=f"settings.update.{key}",
            target_type="setting",
            target_id=key,
            before=before,
            after=value,
        )
        self.db.commit()
        return dict(entry.value)
