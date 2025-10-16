from __future__ import annotations

import secrets
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import AdsClaim, User
from app.services.rate_limiter import RateLimiter


class AdsNonceError(Exception):
    pass


class AdsNonceManager:
    def __init__(self, ttl_seconds: int = 300) -> None:
        self.ttl_seconds = ttl_seconds
        self._store: Dict[str, tuple[UUID, float]] = {}

    def issue(self, user_id: UUID) -> str:
        nonce = secrets.token_urlsafe(24)
        expires_at = time.time() + self.ttl_seconds
        self._store[nonce] = (user_id, expires_at)
        return nonce

    def consume(self, user_id: UUID, nonce: str) -> None:
        record = self._store.pop(nonce, None)
        if record is None:
            raise AdsNonceError("Unknown nonce")
        stored_user, expires_at = record
        if stored_user != user_id:
            raise AdsNonceError("Nonce owner mismatch")
        if expires_at < time.time():
            raise AdsNonceError("Nonce expired")


@dataclass(slots=True)
class ProviderResult:
    valid: bool
    value: int
    meta: Dict[str, Any]


class AdsenseAdapter:
    @staticmethod
    def verify(proof: Dict[str, Any]) -> ProviderResult:
        token = str(proof.get("token", "")).strip()
        if not token or len(token) < 6:
            return ProviderResult(valid=False, value=0, meta={})
        value = int(proof.get("value", 1))
        return ProviderResult(valid=True, value=max(value, 1), meta={"token": token[-6:]})


class MonetagAdapter:
    @staticmethod
    def verify(proof: Dict[str, Any]) -> ProviderResult:
        signature = str(proof.get("signature", "")).strip()
        if signature.lower() != "ok":
            return ProviderResult(valid=False, value=0, meta={})
        value = int(proof.get("value", 2))
        return ProviderResult(valid=True, value=max(value, 1), meta={"signature": "ok"})


PROVIDER_MAP = {
    "adsense": AdsenseAdapter,
    "monetag": MonetagAdapter,
}


class AdsService:
    MAX_DAILY_CLAIMS = 10
    COOLDOWN_SECONDS = 60

    def __init__(self, db: Session, nonce_manager: AdsNonceManager) -> None:
        self.db = db
        self.nonce_manager = nonce_manager
        self._rate_limiter = RateLimiter(requests=20, window_seconds=60)

    def start(self, user: User) -> str:
        self._rate_limiter.check(f"ads-start:{user.id}")
        return self.nonce_manager.issue(user.id)

    def _verify_provider(self, provider: str, proof: Dict[str, Any]) -> ProviderResult:
        adapter_class = PROVIDER_MAP.get(provider)
        if not adapter_class:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported provider")
        result = adapter_class.verify(proof)
        if not result.valid or result.value <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid proof")
        return result

    def _check_caps(self, user: User) -> None:
        now = datetime.now(timezone.utc)
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        stmt = (
            select(func.count(AdsClaim.id))
            .where(AdsClaim.user_id == user.id)
            .where(AdsClaim.claimed_at >= start_of_day)
        )
        claims_today = self.db.scalar(stmt) or 0
        if claims_today >= self.MAX_DAILY_CLAIMS:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Daily ads cap reached")

        last_claim_stmt = (
            select(AdsClaim)
            .where(AdsClaim.user_id == user.id)
            .order_by(AdsClaim.claimed_at.desc())
        )
        last_claim = self.db.scalars(last_claim_stmt).first()
        if last_claim:
            delta = (now - last_claim.claimed_at).total_seconds()
            if delta < self.COOLDOWN_SECONDS:
                raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Claim cooldown active")

    def claim(self, user: User, *, nonce: str, provider: str, proof: Dict[str, Any]) -> AdsClaim:
        self._rate_limiter.check(f"ads-claim:{user.id}")
        try:
            self.nonce_manager.consume(user.id, nonce)
        except AdsNonceError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

        self._check_caps(user)
        result = self._verify_provider(provider, proof)

        user.coins = (user.coins or 0) + result.value
        self.db.add(user)

        claim = AdsClaim(
            user_id=user.id,
            provider=provider,
            nonce=nonce,
            value_coins=result.value,
            claimed_at=datetime.now(timezone.utc),
            meta=result.meta,
        )
        self.db.add(claim)
        self.db.commit()
        self.db.refresh(claim)
        return claim


__all__ = [
    "AdsService",
    "AdsNonceManager",
    "AdsNonceError",
]
