from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.admin.audit import AuditContext
from app.admin.deps import require_perm
from app.admin.schemas import (
    AdsSettingsResponse,
    AdsSettingsUpdateRequest,
    KyaroPromptResponse,
    KyaroPromptUpdateRequest,
)
from app.deps import get_db
from app.models import User
from app.services.settings_store import SettingsStore


router = APIRouter(tags=["admin-settings"])

ADS_KEY = "ads.enabled"
KYARO_PROMPT_KEY = "kyaro.system_prompt"


def _audit_context(request: Request, actor: User) -> AuditContext:
    client_host = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return AuditContext(actor_user_id=actor.id, ip=client_host, ua=user_agent)


@router.get("/settings/ads", response_model=AdsSettingsResponse)
async def get_ads_settings(
    _: User = Depends(require_perm("settings:ads:read")),
    db: Session = Depends(get_db),
) -> AdsSettingsResponse:
    store = SettingsStore(db)
    value = store.get(ADS_KEY, default={"enabled": False})
    return AdsSettingsResponse(enabled=bool(value.get("enabled", False)))


@router.patch("/settings/ads", response_model=AdsSettingsResponse)
async def update_ads_settings(
    request: Request,
    payload: AdsSettingsUpdateRequest,
    actor: User = Depends(require_perm("settings:ads:update")),
    db: Session = Depends(get_db),
) -> AdsSettingsResponse:
    store = SettingsStore(db)
    context = _audit_context(request, actor)
    now = datetime.now(timezone.utc).isoformat()
    value = {
        "enabled": payload.enabled,
        "updated_at": now,
        "updated_by": str(actor.id),
    }
    store.set(ADS_KEY, value, context=context)
    return AdsSettingsResponse(enabled=payload.enabled)


@router.get("/kyaro/prompt", response_model=KyaroPromptResponse)
async def get_kyaro_prompt(
    _: User = Depends(require_perm("kyaro:prompt:read")),
    db: Session = Depends(get_db),
) -> KyaroPromptResponse:
    store = SettingsStore(db)
    value = store.get(KYARO_PROMPT_KEY, default={"prompt": ""})
    updated_by = value.get("updated_by")
    try:
        updated_by_uuid = UUID(updated_by) if updated_by else None
    except ValueError:
        updated_by_uuid = None
    return KyaroPromptResponse(
        prompt=value.get("prompt", ""),
        version=value.get("version"),
        updated_at=value.get("updated_at"),
        updated_by=updated_by_uuid,
    )


@router.patch("/kyaro/prompt", response_model=KyaroPromptResponse)
async def update_kyaro_prompt(
    request: Request,
    payload: KyaroPromptUpdateRequest,
    actor: User = Depends(require_perm("kyaro:prompt:update")),
    db: Session = Depends(get_db),
) -> KyaroPromptResponse:
    store = SettingsStore(db)
    context = _audit_context(request, actor)
    existing = store.get(KYARO_PROMPT_KEY, default={"prompt": "", "version": 0})
    version = int(existing.get("version") or 0) + 1
    now = datetime.now(timezone.utc).isoformat()
    value = {
        "prompt": payload.prompt,
        "version": version,
        "updated_at": now,
        "updated_by": str(actor.id),
    }
    store.set(KYARO_PROMPT_KEY, value, context=context)
    return KyaroPromptResponse(
        prompt=payload.prompt,
        version=version,
        updated_at=now,
        updated_by=actor.id,
    )
