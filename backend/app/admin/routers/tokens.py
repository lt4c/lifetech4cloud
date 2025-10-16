from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.admin.audit import AuditContext
from app.admin.deps import require_perm
from app.admin.schemas import (
    AdminTokenCreateRequest,
    AdminTokenCreateResponse,
    AdminTokenListItem,
)
from app.deps import get_db
from app.models import AdminToken, User
from app.services.token_vault import TokenVaultService


router = APIRouter(tags=["admin-token-vault"])


def _audit_context(request: Request, actor: User) -> AuditContext:
    client_host = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return AuditContext(actor_user_id=actor.id, ip=client_host, ua=user_agent)


def _masked(token: AdminToken) -> str:
    suffix = "••••"
    return f"{token.token_prefix}{suffix}" if token.token_prefix else suffix


@router.get("/tokens", response_model=list[AdminTokenListItem])
async def list_tokens(
    _: User = Depends(require_perm("token:read")),
    db: Session = Depends(get_db),
) -> list[AdminTokenListItem]:
    service = TokenVaultService(db)
    tokens = service.list_tokens()
    return [
        AdminTokenListItem(
            id=token.id,
            label=token.label,
            token_prefix=token.token_prefix,
            masked_token=_masked(token),
            created_at=token.created_at,
            revoked_at=token.revoked_at,
        )
        for token in tokens
    ]


@router.post("/tokens", response_model=AdminTokenCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_token(
    request: Request,
    payload: AdminTokenCreateRequest,
    actor: User = Depends(require_perm("token:create")),
    db: Session = Depends(get_db),
) -> AdminTokenCreateResponse:
    service = TokenVaultService(db)
    context = _audit_context(request, actor)
    record = service.create_token(
        label=payload.label,
        token_plain=payload.token_plain,
        creator_user_id=actor.id,
        context=context,
    )
    return AdminTokenCreateResponse(
        id=record.id,
        label=record.label,
        token_prefix=record.token_prefix,
        token_plain=payload.token_plain,
        created_at=record.created_at,
    )


@router.post("/tokens/{token_id}/revoke", response_model=AdminTokenListItem)
async def revoke_token(
    request: Request,
    token_id: UUID,
    actor: User = Depends(require_perm("token:revoke")),
    db: Session = Depends(get_db),
) -> AdminTokenListItem:
    service = TokenVaultService(db)
    context = _audit_context(request, actor)
    record = service.revoke_token(token_id, context=context)
    return AdminTokenListItem(
        id=record.id,
        label=record.label,
        token_prefix=record.token_prefix,
        masked_token=_masked(record),
        created_at=record.created_at,
        revoked_at=record.revoked_at,
    )
