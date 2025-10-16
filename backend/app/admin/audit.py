from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping
from uuid import UUID

from sqlalchemy.orm import Session

from .models import AuditLog


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
    changes: dict[str, Any] = {}
    all_keys = set(before) | set(after)
    for key in sorted(all_keys):
        before_value = before.get(key)
        after_value = after.get(key)
        if before_value == after_value:
            continue
        changes[key] = {"before": before_value, "after": after_value}
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
    return entry
