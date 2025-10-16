from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models import User

from ..deps import require_perm
from ..schemas import StatusDbResponse, StatusDepsResponse, StatusHealthResponse
from ..services.status import get_db_status, get_dependency_status, get_health_status


router = APIRouter(tags=["admin-status"])


@router.get("/status/health", response_model=StatusHealthResponse)
def health_status(_: User = Depends(require_perm("sys:status:read"))) -> StatusHealthResponse:
    return get_health_status()


@router.get("/status/deps", response_model=StatusDepsResponse)
def deps_status(
    _: User = Depends(require_perm("sys:status:read")),
    db: Session = Depends(get_db),
) -> StatusDepsResponse:
    return get_dependency_status(db)


@router.get("/status/db", response_model=StatusDbResponse)
def db_status(
    _: User = Depends(require_perm("sys:db:read")),
    db: Session = Depends(get_db),
) -> StatusDbResponse:
    return get_db_status(db)
