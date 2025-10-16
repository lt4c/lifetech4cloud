from __future__ import annotations

from typing import Iterable, Sequence, List
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ..audit import AuditContext, record_audit
from ..deps import invalidate_permission_cache_for_role
from ..models import Permission, Role, RolePermission, UserRole
from ..schemas import PermissionDTO, RoleCreate, RoleDTO, RolePermissionsUpdate, RoleUpdate


def _map_role(role: Role, permissions: Sequence[PermissionDTO]) -> RoleDTO:
    return RoleDTO(
        id=role.id,
        name=role.name,
        description=role.description,
        created_at=role.created_at,
        updated_at=role.updated_at,
        permissions=list(permissions),
    )


def _permissions_for_roles(db: Session, role_ids: Iterable[UUID]) -> dict[UUID, list[PermissionDTO]]:
    role_ids = list(role_ids)
    if not role_ids:
        return {}
    stmt = (
        select(RolePermission.role_id, Permission.id, Permission.code, Permission.description)
        .join(Permission, Permission.id == RolePermission.permission_id)
        .where(RolePermission.role_id.in_(role_ids))
    )
    mapping: dict[UUID, list[PermissionDTO]] = {}
    for role_id, perm_id, code, description in db.execute(stmt):
        mapping.setdefault(role_id, []).append(
            PermissionDTO(id=perm_id, code=code, description=description)
        )
    return mapping




def list_all_permissions(db: Session) -> List[PermissionDTO]:
    records = list(db.scalars(select(Permission).order_by(Permission.code)))
    return [PermissionDTO(id=record.id, code=record.code, description=record.description) for record in records]

def list_roles(db: Session) -> list[RoleDTO]:
    roles = list(db.scalars(select(Role).order_by(Role.name)))
    permission_map = _permissions_for_roles(db, [role.id for role in roles])
    return [_map_role(role, permission_map.get(role.id, [])) for role in roles]


def get_role(db: Session, role_id: UUID) -> RoleDTO:
    role = db.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found.")
    permission_map = _permissions_for_roles(db, [role.id])
    return _map_role(role, permission_map.get(role.id, []))


def create_role(db: Session, payload: RoleCreate, context: AuditContext) -> RoleDTO:
    role = Role(name=payload.name, description=payload.description)
    db.add(role)
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create role.") from exc
    db.refresh(role)
    record_audit(
        db,
        context=context,
        action="role.create",
        target_type="role",
        target_id=str(role.id),
        before=None,
        after={"name": role.name, "description": role.description},
    )
    db.commit()
    return get_role(db, role.id)


def update_role(db: Session, role_id: UUID, payload: RoleUpdate, context: AuditContext) -> RoleDTO:
    role = db.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found.")
    before = {"name": role.name, "description": role.description}
    if payload.name is not None:
        role.name = payload.name
    if payload.description is not None:
        role.description = payload.description
    db.add(role)
    db.commit()
    db.refresh(role)
    record_audit(
        db,
        context=context,
        action="role.update",
        target_type="role",
        target_id=str(role.id),
        before=before,
        after={"name": role.name, "description": role.description},
    )
    db.commit()
    return get_role(db, role.id)


def delete_role(db: Session, role_id: UUID, context: AuditContext) -> None:
    role = db.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found.")
    before = {"name": role.name, "description": role.description}
    db.execute(delete(UserRole).where(UserRole.role_id == role_id))
    db.execute(delete(RolePermission).where(RolePermission.role_id == role_id))
    db.delete(role)
    db.commit()
    record_audit(
        db,
        context=context,
        action="role.delete",
        target_type="role",
        target_id=str(role_id),
        before=before,
        after=None,
    )
    db.commit()
    invalidate_permission_cache_for_role(db, role_id)


def set_role_permissions(
    db: Session,
    role_id: UUID,
    payload: RolePermissionsUpdate,
    context: AuditContext,
) -> RoleDTO:
    role = db.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found.")

    before = {
        "permissions": [perm.code for perm in _permissions_for_roles(db, [role_id]).get(role_id, [])]
    }

    desired_codes = {code.strip() for code in payload.permission_codes if code.strip()}

    existing_perms: dict[str, Permission] = {}
    if desired_codes:
        for perm in db.scalars(select(Permission).where(Permission.code.in_(desired_codes))).all():
            existing_perms[perm.code] = perm

    for code in desired_codes:
        if code not in existing_perms:
            perm = Permission(code=code)
            db.add(perm)
            db.flush()
            existing_perms[code] = perm

    db.execute(delete(RolePermission).where(RolePermission.role_id == role_id))
    for code in sorted(desired_codes):
        perm = existing_perms[code]
        db.add(RolePermission(role_id=role_id, permission_id=perm.id))
    db.commit()

    after = {
        "permissions": [perm.code for perm in _permissions_for_roles(db, [role_id]).get(role_id, [])]
    }

    record_audit(
        db,
        context=context,
        action="role.permissions.set",
        target_type="role",
        target_id=str(role_id),
        before=before,
        after=after,
    )
    db.commit()
    invalidate_permission_cache_for_role(db, role_id)
    return get_role(db, role_id)
