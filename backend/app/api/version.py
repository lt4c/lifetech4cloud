from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.deps import get_db
from app.schemas import PlatformVersionResponse
from app.services.settings_store import SettingsStore
from app.services.version_info import (
    DEFAULT_VERSION_ENTRY,
    PLATFORM_VERSION_KEY,
    resolve_version_entry,
)


router = APIRouter(tags=["version"])


@router.get("/version", response_model=PlatformVersionResponse)
async def read_platform_version(db: Session = Depends(get_db)) -> PlatformVersionResponse:
    store = SettingsStore(db)
    value = store.get(PLATFORM_VERSION_KEY, default=DEFAULT_VERSION_ENTRY)
    channel, version, description, _, _ = resolve_version_entry(value)
    return PlatformVersionResponse(channel=channel, version=version, description=description)
