from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from uuid import UUID

from app.models import GiftCode, GiftCodeRedemption, User
from app.services.wallet import WalletService


class GiftCodeService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.wallet = WalletService(db)

    def list_codes(self, *, include_inactive: bool) -> List[GiftCode]:
        stmt = select(GiftCode)
        if not include_inactive:
            stmt = stmt.where(GiftCode.is_active.is_(True))
        stmt = stmt.order_by(GiftCode.created_at.desc())
        return list(self.db.execute(stmt).scalars())

    def get_by_id(self, gift_code_id: UUID) -> GiftCode:
        code = self.db.get(GiftCode, gift_code_id)
        if not code:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="giftcode_not_found")
        return code

    def _normalize_code(self, code: str) -> str:
        normalized = (code or "").strip().upper()
        if not normalized:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="giftcode_code_required")
        if len(normalized) > 64:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="giftcode_code_too_long")
        return normalized

    def _ensure_unique_code(self, normalized_code: str, *, exclude_id: UUID | None = None) -> None:
        stmt = select(GiftCode).where(GiftCode.code == normalized_code)
        if exclude_id is not None:
            stmt = stmt.where(GiftCode.id != exclude_id)
        existing = self.db.execute(stmt).scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="giftcode_code_taken")

    def create_code(
        self,
        *,
        title: str,
        code: str,
        reward_amount: int,
        total_uses: int,
        is_active: bool,
        created_by: UUID | None,
    ) -> GiftCode:
        if reward_amount < 1:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="giftcode_reward_invalid")
        if total_uses < 1:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="giftcode_total_invalid")
        normalized_code = self._normalize_code(code)
        self._ensure_unique_code(normalized_code)

        gift_code = GiftCode(
            title=title.strip(),
            code=normalized_code,
            reward_amount=reward_amount,
            total_uses=total_uses,
            is_active=is_active,
            created_by=created_by,
        )
        self.db.add(gift_code)
        self.db.commit()
        self.db.refresh(gift_code)
        return gift_code

    def update_code(
        self,
        gift_code: GiftCode,
        *,
        title: str | None = None,
        code: str | None = None,
        reward_amount: int | None = None,
        total_uses: int | None = None,
        is_active: bool | None = None,
    ) -> GiftCode:
        if code is not None:
            normalized = self._normalize_code(code)
            if normalized != gift_code.code:
                self._ensure_unique_code(normalized, exclude_id=gift_code.id)
                gift_code.code = normalized
        if title is not None:
            gift_code.title = title.strip()
        if reward_amount is not None:
            if reward_amount < 1:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="giftcode_reward_invalid")
            gift_code.reward_amount = reward_amount
        if total_uses is not None:
            if total_uses < 1:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="giftcode_total_invalid")
            if total_uses < gift_code.redeemed_count:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="giftcode_total_below_redeemed",
                )
            gift_code.total_uses = total_uses
        if is_active is not None:
            gift_code.is_active = bool(is_active)
        gift_code.updated_at = datetime.now(timezone.utc)
        self.db.add(gift_code)
        self.db.commit()
        self.db.refresh(gift_code)
        return gift_code

    def delete_code(self, gift_code: GiftCode) -> None:
        self.db.delete(gift_code)
        self.db.commit()

    def redeem_code(self, *, user: User, code: str) -> tuple[GiftCodeRedemption, GiftCode]:
        normalized_code = self._normalize_code(code)
        stmt = (
            select(GiftCode)
            .where(GiftCode.code == normalized_code)
            .with_for_update()
        )
        gift_code = self.db.execute(stmt).scalar_one_or_none()
        if not gift_code or not gift_code.is_active:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="giftcode_not_found")
        if gift_code.redeemed_count >= gift_code.total_uses:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="giftcode_out_of_stock")

        redemption_stmt = (
            select(GiftCodeRedemption)
            .where(GiftCodeRedemption.gift_code_id == gift_code.id)
            .where(GiftCodeRedemption.user_id == user.id)
            .with_for_update()
        )
        existing = self.db.execute(redemption_stmt).scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="giftcode_already_redeemed")

        self.wallet.adjust_balance(
            user,
            gift_code.reward_amount,
            entry_type="giftcode.redeem",
            ref_id=gift_code.id,
            meta={"code": gift_code.code},
        )

        redemption = GiftCodeRedemption(
            gift_code_id=gift_code.id,
            user_id=user.id,
            reward_amount=gift_code.reward_amount,
        )
        gift_code.redeemed_count += 1
        gift_code.updated_at = datetime.now(timezone.utc)
        self.db.add(redemption)
        self.db.add(gift_code)
        self.db.commit()
        self.db.refresh(redemption)
        self.db.refresh(gift_code)
        return redemption, gift_code


__all__ = ["GiftCodeService"]
