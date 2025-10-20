from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AdReward, LedgerEntry, User, Wallet


@dataclass(slots=True)
class WalletBalance:
    user_id: UUID
    balance: int


class WalletService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_balance(self, user: User) -> WalletBalance:
        wallet = self._get_wallet(user.id, lock=False)
        balance = int(wallet.balance if wallet else user.coins or 0)
        return WalletBalance(user_id=user.id, balance=balance)

    def adjust_balance(
        self,
        user: User,
        amount: int,
        *,
        entry_type: str,
        ref_id: Optional[UUID] = None,
        meta: Optional[dict] = None,
    ) -> WalletBalance:
        wallet = self._get_wallet(user.id, lock=True)
        if wallet is None:
            seed_balance = int(user.coins or 0)
            wallet = Wallet(user_id=user.id, balance=seed_balance)
            self.db.add(wallet)
            self.db.flush()
        else:
            seed_balance = int(wallet.balance or 0)

        new_balance = seed_balance + int(amount)
        if new_balance < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient balance",
            )

        wallet.balance = new_balance
        wallet.updated_at = datetime.now(timezone.utc)
        user.coins = new_balance  # keep legacy field in sync
        self.db.add(wallet)
        self.db.add(user)

        ledger_entry = LedgerEntry(
            user_id=user.id,
            type=entry_type,
            amount=amount,
            balance_after=new_balance,
            ref_id=ref_id,
            meta=meta or {},
        )
        self.db.add(ledger_entry)
        self.db.flush()

        return WalletBalance(user_id=user.id, balance=new_balance)

    def attach_reward_meta(
        self,
        reward: AdReward,
        *,
        placement: Optional[str],
        device_hash: Optional[str],
        meta: Optional[dict],
    ) -> None:
        reward.placement = placement
        reward.device_hash = device_hash
        reward.meta = meta or {}

    def _get_wallet(self, user_id: UUID, *, lock: bool) -> Wallet | None:
        stmt = select(Wallet).where(Wallet.user_id == user_id)
        if lock:
            stmt = stmt.with_for_update()
        result = self.db.execute(stmt).scalar_one_or_none()
        return result


__all__ = [
    "WalletService",
    "WalletBalance",
]
