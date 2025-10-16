from __future__ import annotations

import json
from typing import Any, Iterable, List
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models import User

from ..audit import AuditContext
from ..deps import require_perm
from ..schemas import RoleCreate, RoleDTO, RolePermissionsUpdate, RoleUpdate
from ..services import roles as role_service


router = APIRouter(tags=["admin-roles"])


def _audit_context(request: Request, actor: User) -> AuditContext:
    client_host = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return AuditContext(actor_user_id=actor.id, ip=client_host, ua=user_agent)


async def _load_payload(request: Request) -> dict[str, Any]:
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        body = await request.body()
        return json.loads(body.decode("utf-8")) if body else {}
    form = await request.form()
    data: dict[str, Any] = {}
    for key in form.keys():
        values = form.getlist(key)
        if not values:
            continue
        data[key] = values if len(values) > 1 else values[0]
    return data


def _normalize_permissions(value: Any) -> Iterable[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        parts = [line.strip() for line in value.splitlines() if line.strip()]
        if not parts and value.strip():
            return [value.strip()]
        return parts
    return []


@router.post("/roles", response_model=RoleDTO, status_code=status.HTTP_201_CREATED)
async def create_role(
    request: Request,
    payload: RoleCreate,
    actor: User = Depends(require_perm("role:create")),
    db: Session = Depends(get_db),
) -> RoleDTO:
    context = _audit_context(request, actor)
    return role_service.create_role(db, payload, context)


@router.get("/roles", response_model=list[RoleDTO])
async def list_roles(
    _: User = Depends(require_perm("role:read")),
    db: Session = Depends(get_db),
) -> list[RoleDTO]:
    return role_service.list_roles(db)


@router.get("/roles/{role_id}", response_model=RoleDTO)
async def get_role(
    role_id: UUID,
    _: User = Depends(require_perm("role:read")),
    db: Session = Depends(get_db),
) -> RoleDTO:
    return role_service.get_role(db, role_id)


@router.patch("/roles/{role_id}", response_model=RoleDTO)
async def update_role(
    request: Request,
    role_id: UUID,
    actor: User = Depends(require_perm("role:update")),
    db: Session = Depends(get_db),
) -> RoleDTO:
    raw = await _load_payload(request)
    payload = RoleUpdate(**{k: v for k, v in raw.items() if v is not None})
    context = _audit_context(request, actor)
    return role_service.update_role(db, role_id, payload, context)


@router.delete(
    "/roles/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    response_model=None,
)
async def delete_role(
    request: Request,
    role_id: UUID,
    actor: User = Depends(require_perm("role:delete")),
    db: Session = Depends(get_db),
) -> None:
    context = _audit_context(request, actor)
    role_service.delete_role(db, role_id, context)


@router.put("/roles/{role_id}/perms", response_model=RoleDTO)
async def set_role_permissions(
    request: Request,
    role_id: UUID,
    actor: User = Depends(require_perm("role:set-perms")),
    db: Session = Depends(get_db),
) -> RoleDTO:
    raw = await _load_payload(request)
    codes = list(_normalize_permissions(raw.get("permission_codes", [])))
    new_code = raw.get("new_permission_code")
    if isinstance(new_code, list):
        codes.extend(_normalize_permissions(new_code))
    elif new_code:
        codes.extend(_normalize_permissions(str(new_code)))
    payload = RolePermissionsUpdate(permission_codes=codes)
    context = _audit_context(request, actor)
    return role_service.set_role_permissions(db, role_id, payload, context)
