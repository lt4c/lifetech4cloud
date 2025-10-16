from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse

from sqlalchemy.orm import Session

from app.deps import get_ads_nonce_manager, get_current_user, get_db
from app.models import User
from app.services.ads import AdsService
from app.services.settings_store import SettingsStore
from app.settings import get_settings

router = APIRouter(prefix="/ads", tags=["ads"])


def _ensure_ads_enabled(db: Session) -> None:
    settings = get_settings()
    if not settings.is_feature_enabled("ads"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ads feature disabled")
    store = SettingsStore(db)
    record = store.get("ads.enabled", default={"enabled": False})
    if not record.get("enabled"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ads rewards disabled")


@router.post("/start")
async def start_ads(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    nonce_manager=Depends(get_ads_nonce_manager),
) -> JSONResponse:
    _ensure_ads_enabled(db)
    service = AdsService(db, nonce_manager)
    nonce = service.start(user)
    return JSONResponse({"nonce": nonce})


@router.post("/claim")
async def claim_ads(
    payload: Dict[str, Any],
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    nonce_manager=Depends(get_ads_nonce_manager),
) -> JSONResponse:
    _ensure_ads_enabled(db)
    nonce = payload.get("nonce")
    provider = payload.get("provider")
    proof = payload.get("proof") or {}
    if not nonce or not provider:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing nonce or provider")
    service = AdsService(db, nonce_manager)
    claim = service.claim(user, nonce=str(nonce), provider=str(provider), proof=dict(proof))
    return JSONResponse(
        {
            "claim": {
                "id": str(claim.id),
                "provider": claim.provider,
                "value_coins": claim.value_coins,
                "claimed_at": claim.claimed_at.isoformat() if claim.claimed_at else None,
            },
            "balance": user.coins,
        },
        status_code=status.HTTP_201_CREATED,
    )
