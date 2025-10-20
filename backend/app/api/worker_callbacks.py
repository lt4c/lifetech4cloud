from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.deps import get_db, get_event_bus
from app.models import AdminToken, User, VpsSession, Worker
from app.security.crypto import decrypt_secret, verify_worker_signature
from app.services.event_bus import SessionEventBus
from app.services.wallet import WalletService

callbacks_router = APIRouter(prefix="/workers/callback", tags=["worker-callbacks"])
workers_router = APIRouter(prefix="/workers", tags=["workers"])

CLOCK_SKEW_SECONDS = 300


def _parse_timestamp(raw: str) -> float:
    try:
        return float(raw)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid timestamp") from exc



@workers_router.post("/register")
async def worker_register(
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
) -> JSONResponse:
    token_id = payload.get("token_id")
    admin_token_plain = payload.get("admin_token")
    base_url = payload.get("base_url")
    name = payload.get("name")
    if not token_id or not admin_token_plain or not base_url:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing registration fields")
    try:
        token_uuid = UUID(str(token_id))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token id") from exc
    token = db.get(AdminToken, token_uuid)
    if not token or token.revoked_at:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token unavailable")
    secret = decrypt_secret(token.token_ciphertext)
    if secret != admin_token_plain:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token mismatch")
    normalized_url = str(base_url).rstrip('/')
    existing_stmt = select(Worker).where(Worker.token_id == token_uuid, Worker.base_url == normalized_url)
    existing = db.scalars(existing_stmt).first()
    if existing:
        worker = existing
        if name:
            worker.name = name
        worker.base_url = normalized_url
        worker.status = "idle"
        worker.last_heartbeat = datetime.now(timezone.utc)
    else:
        worker = Worker(name=name, base_url=normalized_url, token_id=token_uuid, status="idle")
        db.add(worker)
    db.commit()
    db.refresh(worker)
    return JSONResponse({"worker_id": str(worker.id)})


async def _verify_request(request: Request, db: Session) -> tuple[Worker, bytes]:
    worker_id_header = request.headers.get("X-Worker-Id")
    timestamp_header = request.headers.get("X-Timestamp")
    signature_header = request.headers.get("X-Signature")
    if not worker_id_header or not timestamp_header or not signature_header:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing worker signature headers")
    try:
        worker_uuid = UUID(worker_id_header)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid worker id") from exc
    worker = db.get(Worker, worker_uuid)
    if not worker or not worker.token_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unknown worker")
    token = db.get(AdminToken, worker.token_id)
    if not token or token.revoked_at:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Worker token revoked")
    body = await request.body()
    timestamp_value = _parse_timestamp(timestamp_header)
    now = datetime.now(timezone.utc).timestamp()
    if abs(now - timestamp_value) > CLOCK_SKEW_SECONDS:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Clock skew too large")
    secret = decrypt_secret(token.token_ciphertext)
    if not verify_worker_signature(secret, body, timestamp_header, signature_header):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")
    return worker, body


def _load_session(db: Session, session_id: UUID) -> VpsSession:
    session = db.get(VpsSession, session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session


@callbacks_router.post("/status")
async def worker_status(
    request: Request,
    db: Session = Depends(get_db),
) -> JSONResponse:
    worker, body = await _verify_request(request, db)
    payload = json.loads(body.decode("utf-8"))
    current_jobs = int(payload.get("current_jobs", worker.current_jobs or 0))
    worker.current_jobs = current_jobs
    worker.last_net_mbps = payload.get("net_mbps")
    worker.last_req_rate = payload.get("req_rate")
    worker.last_heartbeat = datetime.now(timezone.utc)
    worker.status = "busy" if current_jobs > 0 else "idle"
    db.add(worker)
    db.commit()
    return JSONResponse({"ok": True})


@callbacks_router.post("/checklist")
async def worker_checklist(
    request: Request,
    db: Session = Depends(get_db),
    event_bus: SessionEventBus = Depends(get_event_bus),
) -> JSONResponse:
    worker, body = await _verify_request(request, db)
    payload = json.loads(body.decode("utf-8"))
    session_id = payload.get("session_id")
    if not session_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing session_id")
    session_uuid = UUID(str(session_id))
    session = _load_session(db, session_uuid)
    items = payload.get("items") or []
    session.checklist = items
    session.updated_at = datetime.now(timezone.utc)
    db.add(session)
    db.commit()
    await event_bus.publish(
        session.id,
        {
            "event": "checklist.update",
            "data": {"items": items},
        },
    )
    return JSONResponse({"ok": True})


@callbacks_router.post("/result")
async def worker_result(
    request: Request,
    db: Session = Depends(get_db),
    event_bus: SessionEventBus = Depends(get_event_bus),
) -> JSONResponse:
    worker, body = await _verify_request(request, db)
    payload = json.loads(body.decode("utf-8"))
    session_id = payload.get("session_id")
    if not session_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing session_id")
    session_uuid = UUID(str(session_id))
    session = _load_session(db, session_uuid)

    status_value = payload.get("status")
    now = datetime.now(timezone.utc)
    user: User | None = db.get(User, session.user_id) if session.user_id else None

    if status_value == "ready":
        session.status = "ready"
        session.rdp_host = payload.get("rdp_host")
        session.rdp_port = payload.get("rdp_port")
        session.rdp_user = payload.get("rdp_user")
        session.rdp_password = payload.get("rdp_password")
        session.log_url = payload.get("log_url")
        session.updated_at = now
    elif status_value == "failed":
        session.status = "failed"
        session.updated_at = now
        if user and session.product:
            WalletService(db).adjust_balance(
                user,
                session.product.price_coins,
                entry_type="vps.refund",
                ref_id=session.id,
                meta={"reason": "worker_failed"},
            )
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status")

    if worker.current_jobs:
        worker.current_jobs = max(worker.current_jobs - 1, 0)
    worker.status = "busy" if worker.current_jobs else "idle"
    worker.last_heartbeat = now
    db.add(worker)
    db.add(session)
    db.commit()

    await event_bus.publish(
        session.id,
        {
            "event": "status.update",
            "data": {"status": session.status},
        },
    )
    if session.status == "ready":
        ready_payload = {
            "rdp_host": session.rdp_host,
            "rdp_port": session.rdp_port,
            "rdp_user": session.rdp_user,
            "rdp_password": session.rdp_password,
            "log_url": session.log_url,
        }
        await event_bus.publish(
            session.id,
            {
                "event": "ready",
                "data": ready_payload,
            },
        )
    elif session.status == "failed":
        await event_bus.publish(
            session.id,
            {
                "event": "failed",
                "data": {"message": payload.get("message", "Worker reported failure")},
            },
        )

    return JSONResponse({"ok": True})


__all__ = ['workers_router', 'callbacks_router']

