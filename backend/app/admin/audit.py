from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Mapping, Sequence
from uuid import UUID

import json
import os
from pathlib import Path
from sqlalchemy.orm import Session

from .models import AuditLog


_AUDIT_LOG_FILE = Path(__file__).resolve().parents[3] / "admin-actions.log"


def _append_audit_file(payload: dict) -> None:
    try:
        line = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        os.makedirs(_AUDIT_LOG_FILE.parent, exist_ok=True)
        with open(_AUDIT_LOG_FILE, "a", encoding="utf-8") as fp:
            fp.write(line + "\n")
            # Đảm bảo dữ liệu được ghi ngay lập tức vào đĩa
            fp.flush()
            os.fsync(fp.fileno())
    except Exception as e:
        # Best effort: file logging must not break request flow
        import logging
        logging.error(f"Failed to write audit log: {e}")


@dataclass(slots=True)
class AuditContext:
    actor_user_id: UUID | None
    ip: str | None
    ua: str | None


def diff_dict(before: Mapping[str, Any] | None, after: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if before is None and after is None:
        return None
    before = before or {}
    after = after or {}

    def _normalize(value: Any) -> Any:
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, (UUID, Decimal)):
            return str(value)
        if isinstance(value, Mapping):
            return {key: _normalize(val) for key, val in value.items()}
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            return [_normalize(item) for item in value]
        return value

    changes: dict[str, Any] = {}
    all_keys = set(before) | set(after)
    for key in sorted(all_keys):
        before_value = before.get(key)
        after_value = after.get(key)
        if before_value == after_value:
            continue
        changes[key] = {"before": _normalize(before_value), "after": _normalize(after_value)}
    return changes or None


def record_audit(
    db: Session,
    *,
    context: AuditContext,
    action: str,
    target_type: str,
    target_id: str | None,
    before: Mapping[str, Any] | None = None,
    after: Mapping[str, Any] | None = None,
) -> AuditLog:
    entry = AuditLog(
        actor_user_id=context.actor_user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        diff_json=diff_dict(before, after),
        ip=context.ip,
        ua=context.ua,
    )
    db.add(entry)
    # File sink (JSONL)
    try:
        payload = {
            "ts": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "actor_user_id": str(context.actor_user_id) if context.actor_user_id else None,
            "action": action,
            "target_type": target_type,
            "target_id": target_id,
            "ip": context.ip,
            "ua": context.ua,
            "diff": diff_dict(before, after),
        }
        _append_audit_file(payload)
    except Exception:
        pass
    return entry
