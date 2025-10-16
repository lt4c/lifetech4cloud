from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models import User

from ..audit import AuditContext
from ..deps import require_perm
from ..schemas import (
    AdminUser,
    UserCoinsUpdateRequest,
    UserCreate,
    UserListResponse,
    UserQueryParams,
    UserUpdate,
)
from ..services import users as user_service


router = APIRouter(tags=["admin-users"])


def _audit_context(request: Request, actor: User) -> AuditContext:
    client_host = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return AuditContext(actor_user_id=actor.id, ip=client_host, ua=user_agent)


async def _parse_user_update(request: Request) -> UserUpdate:
    content_type = request.headers.get("content-type", "")
    data: dict[str, Any]
    if "application/json" in content_type:
        body = await request.body()
        data = json.loads(body.decode("utf-8")) if body else {}
    else:
        form = await request.form()
        data = {key: form.get(key) for key in form.keys()}
    return UserUpdate(**{k: v for k, v in data.items() if v is not None})


async def _parse_role_payload(request: Request) -> list[UUID]:
    content_type = request.headers.get("content-type", "")
    role_ids: list[UUID] = []
    if "application/json" in content_type:
        payload = await request.json()
        values = payload.get("role_ids", []) if isinstance(payload, dict) else []
    else:
        form = await request.form()
        values = form.getlist("role_ids")
    for value in values:
        try:
            role_ids.append(UUID(str(value)))
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid role id: {value}")
    return role_ids


@router.post("/users", response_model=AdminUser, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: Request,
    payload: UserCreate,
    actor: User = Depends(require_perm("user:create")),
    db: Session = Depends(get_db),
) -> AdminUser:
    context = _audit_context(request, actor)
    return user_service.create_user(db, payload, context)


@router.get("/users", response_model=UserListResponse)
async def list_users(
    q: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    role: UUID | None = Query(None),
    _: User = Depends(require_perm("user:read")),
    db: Session = Depends(get_db),
) -> UserListResponse:
    params = UserQueryParams(q=q, page=page, page_size=page_size, role=role)
    return user_service.list_users(db, params)


@router.get("/users/{user_id}", response_model=AdminUser)
async def get_user(
    user_id: UUID,
    _: User = Depends(require_perm("user:read")),
    db: Session = Depends(get_db),
) -> AdminUser:
    return user_service.get_user(db, user_id)


@router.patch("/users/{user_id}", response_model=AdminUser)
async def update_user(
    request: Request,
    user_id: UUID,
    actor: User = Depends(require_perm("user:update")),
    db: Session = Depends(get_db),
) -> AdminUser:
    payload = await _parse_user_update(request)
    context = _audit_context(request, actor)
    return user_service.update_user(db, user_id, payload, context)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response, response_model=None)
async def delete_user(
    request: Request,
    user_id: UUID,
    actor: User = Depends(require_perm("user:delete")),
    db: Session = Depends(get_db),
) -> None:
    context = _audit_context(request, actor)
    user_service.delete_user(db, user_id, context)


@router.post("/users/{user_id}/roles", response_model=AdminUser)
async def assign_roles(
    request: Request,
    user_id: UUID,
    actor: User = Depends(require_perm("user:assign-role")),
    db: Session = Depends(get_db),
) -> AdminUser:
    role_ids = await _parse_role_payload(request)
    context = _audit_context(request, actor)
    return user_service.add_roles_to_user(db, user_id, role_ids, context)


@router.delete("/users/{user_id}/roles", response_model=AdminUser)
async def remove_roles(
    request: Request,
    user_id: UUID,
    actor: User = Depends(require_perm("user:assign-role")),
    db: Session = Depends(get_db),
) -> AdminUser:
    role_ids = await _parse_role_payload(request)
    context = _audit_context(request, actor)
    return user_service.remove_roles_from_user(db, user_id, role_ids, context)

@router.patch("/users/{user_id}/coins", response_model=AdminUser)
async def update_user_coins_endpoint(
    request: Request,
    user_id: UUID,
    payload: UserCoinsUpdateRequest,
    actor: User = Depends(require_perm("user:coins:update")),
    db: Session = Depends(get_db),
) -> AdminUser:
    context = _audit_context(request, actor)
    return user_service.update_user_coins(
        db,
        user_id,
        operation=payload.op,
        amount=payload.amount,
        reason=payload.reason,
        context=context,
    )
