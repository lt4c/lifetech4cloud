from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.admin.deps import require_perm
from app.admin.schemas import (
    GiftCodeCreateRequest,
    GiftCodeDTO,
    GiftCodeUpdateRequest,
)
from app.deps import get_db
from app.models import User
from app.services.giftcodes import GiftCodeService

router = APIRouter(tags=["admin-giftcodes"])


def _dto(code) -> GiftCodeDTO:
    return GiftCodeDTO(
        id=code.id,
        title=code.title,
        code=code.code,
        reward_amount=code.reward_amount,
        total_uses=code.total_uses,
        redeemed_count=code.redeemed_count,
        is_active=code.is_active,
        created_by=code.created_by,
        created_at=code.created_at,
        updated_at=code.updated_at,
    )


@router.get("/giftcodes", response_model=List[GiftCodeDTO])
async def list_gift_codes(
    include_inactive: bool = Query(True),
    _: User = Depends(require_perm("gift_code:read")),
    db: Session = Depends(get_db),
) -> List[GiftCodeDTO]:
    service = GiftCodeService(db)
    codes = service.list_codes(include_inactive=include_inactive)
    return [_dto(code) for code in codes]


@router.post("/giftcodes", response_model=GiftCodeDTO, status_code=status.HTTP_201_CREATED)
async def create_gift_code(
    payload: GiftCodeCreateRequest,
    actor: User = Depends(require_perm("gift_code:create")),
    db: Session = Depends(get_db),
) -> GiftCodeDTO:
    service = GiftCodeService(db)
    code = service.create_code(
        title=payload.title,
        code=payload.code,
        reward_amount=payload.reward_amount,
        total_uses=payload.total_uses,
        is_active=payload.is_active,
        created_by=actor.id,
    )
    return _dto(code)


@router.patch("/giftcodes/{gift_code_id}", response_model=GiftCodeDTO)
async def update_gift_code(
    gift_code_id: UUID,
    payload: GiftCodeUpdateRequest,
    _: User = Depends(require_perm("gift_code:update")),
    db: Session = Depends(get_db),
) -> GiftCodeDTO:
    service = GiftCodeService(db)
    code = service.get_by_id(gift_code_id)
    updated = service.update_code(
        code,
        title=payload.title,
        code=payload.code,
        reward_amount=payload.reward_amount,
        total_uses=payload.total_uses,
        is_active=payload.is_active,
    )
    return _dto(updated)


@router.delete("/giftcodes/{gift_code_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_gift_code(
    gift_code_id: UUID,
    _: User = Depends(require_perm("gift_code:delete")),
    db: Session = Depends(get_db),
) -> None:
    service = GiftCodeService(db)
    code = service.get_by_id(gift_code_id)
    service.delete_code(code)
