from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.deps import get_db
from app.services.settings_store import SettingsStore

BANNER_MESSAGE_KEY = "platform.banner_message"

router = APIRouter(tags=["banner"])


@router.get("/banner")
async def read_banner_message(db: Session = Depends(get_db)) -> dict[str, str | None]:
    store = SettingsStore(db)
    value = store.get(BANNER_MESSAGE_KEY, default={"message": ""})
    message = (value.get("message") or "").strip()
    updated_at = value.get("updated_at")
    if not message:
        return {"message": "", "updated_at": updated_at}
    return {"message": message, "updated_at": updated_at}
