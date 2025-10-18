from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.deps import get_db

from ..deps import require_perm
from ..services import roles as role_service

router = APIRouter(default_response_class=HTMLResponse)


@router.get("/roles/{role_id}", name="admin_role_detail_view")
def admin_role_detail_view(
    role_id: UUID,
    actor=Depends(require_perm("role:read")),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    role = role_service.get_role(db, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found.")
    body = (
        f"<html><head><title>{role.name}</title></head>"
        f"<body><h1>{role.name}</h1>"
        f"<p>{role.description or ''}</p>"
        "</body></html>"
    )
    return HTMLResponse(content=body, status_code=200)
