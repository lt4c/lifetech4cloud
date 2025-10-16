from __future__ import annotations

import uuid
from typing import Generator

from fastapi import Depends, HTTPException, Request, status

from app.services.ads import AdsNonceManager
from app.services.event_bus import SessionEventBus
from app.services.support_event_bus import SupportEventBus
from app.services.kyaro import KyaroAssistant
from app.services.worker_client import WorkerClient
from sqlalchemy.orm import Session

from .db import SessionLocal
from .models import User
from .settings import get_settings
from .utils import is_bad_signature, verify_session


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_session_cookie(request: Request) -> str | None:
    settings = get_settings()
    return request.cookies.get(settings.session_cookie_name)


async def get_current_user(
    request: Request, db: Session = Depends(get_db)
) -> User:
    settings = get_settings()
    token = get_session_cookie(request)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated.")
    try:
        payload = verify_session(settings.secret_key, token)
    except Exception as exc:  # pragma: no cover - defensive
        if is_bad_signature(exc):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session.") from exc
        raise
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session.")
    try:
        user_uuid = uuid.UUID(str(user_id))
    except ValueError as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session.") from exc
    user = db.get(User, user_uuid)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.")
    return user


def get_event_bus(request: Request) -> SessionEventBus:
    bus = getattr(request.app.state, "event_bus", None)
    if not bus:
        raise RuntimeError("SessionEventBus not initialised")
    return bus


def get_support_bus(request: Request) -> SupportEventBus:
    bus = getattr(request.app.state, "support_bus", None)
    if not bus:
        raise RuntimeError("SupportEventBus not initialised")
    return bus


def get_worker_client(request: Request) -> WorkerClient:
    client = getattr(request.app.state, "worker_client", None)
    if not client:
        raise RuntimeError("WorkerClient not initialised")
    return client


def get_ads_nonce_manager(request: Request) -> AdsNonceManager:
    manager = getattr(request.app.state, "ads_nonce_manager", None)
    if not manager:
        raise RuntimeError("AdsNonceManager not initialised")
    return manager


def get_kyaro_assistant(request: Request) -> KyaroAssistant:
    assistant = getattr(request.app.state, "kyaro_assistant", None)
    if not assistant:
        raise RuntimeError("KyaroAssistant not initialised")
    return assistant

