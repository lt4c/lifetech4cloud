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
    BannerMessageResponse,
    BannerMessageUpdateRequest,
    KyaroPromptResponse,
    KyaroPromptUpdateRequest,
    VersionInfoResponse,
    VersionInfoUpdateRequest,
)
from app.deps import get_db
from app.models import User
from app.services.settings_store import SettingsStore
from app.services.version_info import (
    DEFAULT_VERSION_ENTRY,
    PLATFORM_VERSION_KEY,
    VERSION_DESCRIPTIONS,
    resolve_version_entry,
)


router = APIRouter(tags=["admin-settings"])

ADS_KEY = "ads.enabled"
KYARO_PROMPT_KEY = "kyaro.system_prompt"
BANNER_MESSAGE_KEY = "platform.banner_message"


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


@router.get("/settings/banner", response_model=BannerMessageResponse)
async def get_banner_message(
    _: User = Depends(require_perm("settings:banner:read")),
    db: Session = Depends(get_db),
) -> BannerMessageResponse:
    store = SettingsStore(db)
    value = store.get(BANNER_MESSAGE_KEY, default={"message": ""})
    message = value.get("message", "")
    updated_by = value.get("updated_by")
    try:
        updated_by_uuid = UUID(updated_by) if updated_by else None
    except ValueError:
        updated_by_uuid = None
    return BannerMessageResponse(
        message=message,
        updated_at=value.get("updated_at"),
        updated_by=updated_by_uuid,
    )


@router.patch("/settings/banner", response_model=BannerMessageResponse)
async def update_banner_message(
    request: Request,
    payload: BannerMessageUpdateRequest,
    actor: User = Depends(require_perm("settings:banner:update")),
    db: Session = Depends(get_db),
) -> BannerMessageResponse:
    store = SettingsStore(db)
    context = _audit_context(request, actor)
    message = payload.message if payload.message is not None else ""
    now = datetime.now(timezone.utc).isoformat()
    value = {
        "message": message,
        "updated_at": now,
        "updated_by": str(actor.id),
    }
    store.set(BANNER_MESSAGE_KEY, value, context=context)
    return BannerMessageResponse(message=message, updated_at=now, updated_by=actor.id)


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


@router.get("/settings/version", response_model=VersionInfoResponse)
async def get_platform_version(
    _: User = Depends(require_perm("settings:version:read")),
    db: Session = Depends(get_db),
) -> VersionInfoResponse:
    store = SettingsStore(db)
    value = store.get(
        PLATFORM_VERSION_KEY,
        default=DEFAULT_VERSION_ENTRY,
    )
    channel, version, description, updated_at, updated_by = resolve_version_entry(value)
    return VersionInfoResponse(
        channel=channel, version=version, description=description, updated_at=updated_at, updated_by=updated_by
    )


@router.patch("/settings/version", response_model=VersionInfoResponse)
async def update_platform_version(
    request: Request,
    payload: VersionInfoUpdateRequest,
    actor: User = Depends(require_perm("settings:version:update")),
    db: Session = Depends(get_db),
) -> VersionInfoResponse:
    channel = payload.channel
    version = payload.version.strip()
    description = VERSION_DESCRIPTIONS.get(channel, VERSION_DESCRIPTIONS["dev"])

    store = SettingsStore(db)
    context = _audit_context(request, actor)
    now = datetime.now(timezone.utc).isoformat()
    value = {
        "channel": channel,
        "version": version,
        "updated_at": now,
        "updated_by": str(actor.id),
    }
    store.set(PLATFORM_VERSION_KEY, value, context=context)

    return VersionInfoResponse(
        channel=channel,
        version=version,
        description=description,
        updated_at=datetime.fromisoformat(now),
        updated_by=actor.id,
    )
