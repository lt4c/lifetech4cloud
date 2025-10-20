from __future__ import annotations

import base64
import hashlib
import hmac
import ipaddress
import json
import logging
import secrets
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple
from uuid import UUID

import httpx
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.metrics import (
    rewarded_ads_daily_cap,
    rewarded_ads_duration_seconds,
    rewarded_ads_failure_ratio,
    rewarded_ads_prepare_total,
    rewarded_ads_reward_amount,
    rewarded_ads_ssv_total,
)
from app.models import AdReward, User, UserLimit
from app.services.rate_limiter import RateLimiter
from app.services.wallet import WalletService
from app.settings import Settings, get_settings

try:
    from redis import Redis  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    Redis = None

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_public_key

logger = logging.getLogger(__name__)

NONCE_REDIS_PREFIX = "ads:nonce"
EVENT_REDIS_PREFIX = "ads:event"
FAIL_STAT_REDIS_PREFIX = "ads:ssv:fail"
SUCCESS_STAT_REDIS_PREFIX = "ads:ssv:success"
CAP_REDIS_KEY = "ads:cap:effective"


class AdsNonceError(Exception):
    pass


@dataclass(slots=True)
class NonceRecord:
    user_id: UUID
    device_hash: str
    placement: str
    issued_at: datetime


class AdsNonceManager:
    def __init__(
        self,
        ttl_seconds: int = 600,
        *,
        redis_client: Optional["Redis"] = None,
    ) -> None:
        self.ttl_seconds = ttl_seconds
        self._redis = redis_client if Redis is not None else None
        self._store: Dict[str, Tuple[str, str, str, float]] = {}

    def issue(self, user_id: UUID, device_hash: str, placement: str) -> str:
        nonce = secrets.token_urlsafe(32)
        issued_at = time.time()
        payload = json.dumps(
            {
                "uid": str(user_id),
                "device": device_hash,
                "placement": placement,
                "iat": issued_at,
            }
        )
        if self._redis is not None:
            key = self._redis_key(nonce)
            try:
                self._redis.setex(key, self.ttl_seconds, payload)
            except Exception:  # pragma: no cover - fallback in case redis unavailable
                logger.warning("Failed to persist nonce in redis; falling back to memory store.")
                self._store[nonce] = (str(user_id), device_hash, placement, issued_at + self.ttl_seconds)
            else:
                return nonce

        self._store[nonce] = (str(user_id), device_hash, placement, issued_at + self.ttl_seconds)
        return nonce

    def consume(self, user_id: UUID, nonce: str) -> NonceRecord:
        payload: Optional[str] = None
        if self._redis is not None:
            try:
                payload = self._redis.getdel(self._redis_key(nonce))
            except Exception:  # pragma: no cover - fallback if redis unavailable
                payload = None
        if payload:
            try:
                raw = json.loads(payload)
            except json.JSONDecodeError as exc:  # pragma: no cover - defensive
                raise AdsNonceError("Corrupted nonce payload") from exc
            return self._build_record(user_id, nonce, raw)

        record = self._store.pop(nonce, None)
        if not record:
            raise AdsNonceError("Unknown nonce")
        stored_user_id, device_hash, placement, expires_at = record
        if expires_at < time.time():
            raise AdsNonceError("Nonce expired")
        if stored_user_id != str(user_id):
            raise AdsNonceError("Nonce owner mismatch")
        return NonceRecord(
            user_id=user_id,
            device_hash=device_hash,
            placement=placement,
            issued_at=datetime.fromtimestamp(expires_at - self.ttl_seconds, tz=timezone.utc),
        )

    def _redis_key(self, nonce: str) -> str:
        return f"{NONCE_REDIS_PREFIX}:{nonce}"

    def _build_record(self, user_id: UUID, nonce: str, raw: Dict[str, Any]) -> NonceRecord:
        stored_uid = raw.get("uid")
        if stored_uid != str(user_id):
            raise AdsNonceError("Nonce owner mismatch")
        device_hash = str(raw.get("device") or "")
        placement = str(raw.get("placement") or "")
        issued_at = datetime.fromtimestamp(float(raw.get("iat", time.time())), tz=timezone.utc)
        return NonceRecord(
            user_id=user_id,
            device_hash=device_hash,
            placement=placement,
            issued_at=issued_at,
        )


class SSVSignatureVerifier:
    def __init__(self, settings: Settings) -> None:
        self._secret = (settings.ssv_secret or "").strip() or None
        self._public_key = None
        public_key_path = (settings.ssv_public_key_path or "").strip()
        if public_key_path:
            try:
                with open(public_key_path, "rb") as handle:
                    self._public_key = load_pem_public_key(handle.read())
            except FileNotFoundError:
                logger.error("Public key path configured but file not found: %s", public_key_path)
            except Exception:  # pragma: no cover - defensive
                logger.exception("Failed to load SSV public key")

        if not self._secret and not self._public_key:
            logger.warning("No SSV secret or public key configured; SSV verification will fail.")

    def verify(
        self,
        *,
        event_id: str,
        uid: str,
        nonce: str,
        amount: int,
        duration: int,
        device_hash: str | None,
        placement: str | None,
        signature: str,
    ) -> None:
        payload_parts = [
            f"eventId={event_id}",
            f"uid={uid}",
            f"nonce={nonce}",
            f"amount={amount}",
            f"duration={duration}",
        ]
        if placement:
            payload_parts.append(f"placement={placement}")
        if device_hash:
            payload_parts.append(f"device={device_hash}")
        payload = "|".join(payload_parts).encode("utf-8")

        if self._secret:
            expected = hmac.new(self._secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
            if not hmac.compare_digest(expected, signature):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid signature",
                )
            return

        if self._public_key is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SSV verification unavailable",
            )

        try:
            signature_bytes = base64.urlsafe_b64decode(signature + "===")
            self._public_key.verify(
                signature_bytes,
                payload,
                padding.PKCS1v15(),
                hashes.SHA256(),
            )
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid signature",
            ) from exc


@dataclass(slots=True)
class PrepareContext:
    placement: str
    device_hash: str
    client_nonce: str
    timestamp: str
    signature: str
    recaptcha_token: Optional[str]
    ip: str
    user_agent: str
    client_hints: Dict[str, str]
    referer_path: str
    asn: Optional[str]


@dataclass(slots=True)
class LimitsSnapshot:
    user_limits: Optional[UserLimit]
    device_limits: Optional[UserLimit]

    @property
    def last_reward_at(self) -> Optional[datetime]:
        candidates = []
        if self.user_limits and self.user_limits.last_reward_at:
            candidates.append(self.user_limits.last_reward_at)
        if self.device_limits and self.device_limits.last_reward_at:
            candidates.append(self.device_limits.last_reward_at)
        if not candidates:
            return None
        return max(candidates)


class AdsService:
    def __init__(
        self,
        db: Session,
        nonce_manager: AdsNonceManager,
        *,
        redis_client: Optional["Redis"],
        settings: Optional[Settings] = None,
    ) -> None:
        self.db = db
        self.nonce_manager = nonce_manager
        self.settings = settings or get_settings()
        self.redis = redis_client if Redis is not None else None
        self.signature_verifier = SSVSignatureVerifier(self.settings)
        self.prepare_limiter = RateLimiter(
            requests=20,
            window_seconds=2,
            redis_client=self.redis,
            prefix="ads:prepare",
        )
        self.ssv_limiter = RateLimiter(
            requests=5,
            window_seconds=10,
            redis_client=self.redis,
            prefix="ads:ssv",
        )

    def prepare(self, user: User, ctx: PrepareContext) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        self.prepare_limiter.check(f"ip:{ctx.ip}")
        self.prepare_limiter.check(f"user:{user.id}")

        self._enforce_route(ctx.referer_path)
        self._enforce_ip_policy(ctx.ip, ctx.asn)
        self._verify_client_signature(user_id=user.id, ctx=ctx, now=now)
        self._verify_recaptcha(ctx, user_id=user.id)

        limits = self._fetch_limits_snapshot(user.id, ctx.device_hash, now.date())
        self._ensure_not_on_cooldown(limits, now)
        self._ensure_cap_available(limits, ctx.device_hash)
        if ctx.placement not in self.settings.allowed_placements:
            rewarded_ads_prepare_total.labels(status="placement").inc()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid placement")

        nonce = self.nonce_manager.issue(user.id, ctx.device_hash, ctx.placement)
        ad_tag_url = self._build_ad_tag_url(user.id, nonce, ctx.placement, ctx.device_hash)
        rewarded_ads_prepare_total.labels(status="ok").inc()
        return {
            "nonce": nonce,
            "adTagUrl": ad_tag_url,
            "expiresIn": self.nonce_manager.ttl_seconds,
            "priceFloor": self.settings.price_floor or 0,
        }

    def handle_ssv(self, payload: Dict[str, Any], *, ip: str) -> Dict[str, Any]:
        self.ssv_limiter.check(f"ip:{ip}")
        event_id = str(payload.get("eventId") or payload.get("event_id") or "").strip()
        uid_raw = str(payload.get("uid") or payload.get("userId") or "").strip()
        nonce = str(payload.get("nonce") or "").strip()
        amount = int(payload.get("amount") or 0)
        duration = int(payload.get("duration") or payload.get("durationSec") or 0)
        signature = str(payload.get("sig") or payload.get("signature") or "").strip()
        network = str(payload.get("network") or payload.get("provider") or "gam").strip().lower() or "gam"
        placement = str(payload.get("placement") or "").strip() or None
        device_hash = str(payload.get("device") or payload.get("deviceHash") or "").strip() or None

        if not event_id or not uid_raw or not nonce or not signature:
            rewarded_ads_ssv_total.labels(status="invalid").inc()
            self._register_failure()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing required parameters")

        try:
            user_id = UUID(uid_raw)
        except ValueError as exc:
            rewarded_ads_ssv_total.labels(status="invalid").inc()
            self._register_failure()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid uid") from exc

        user = self.db.get(User, user_id)
        if not user:
            rewarded_ads_ssv_total.labels(status="invalid").inc()
            self._register_failure()
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        if amount != self.settings.reward_amount:
            rewarded_ads_ssv_total.labels(status="invalid").inc()
            self._register_failure()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid reward amount")
        if duration < self.settings.required_duration:
            rewarded_ads_ssv_total.labels(status="invalid").inc()
            self._register_failure()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Duration too short")

        existing_reward = self._get_reward_by_event(event_id)
        if existing_reward:
            balance = WalletService(self.db).get_balance(user).balance
            rewarded_ads_ssv_total.labels(status="duplicate").inc()
            return {"ok": True, "added": 0, "balance": balance, "duplicate": True}

        if not self._claim_event(event_id):
            existing_reward = self._get_reward_by_event(event_id)
            if existing_reward:
                balance = WalletService(self.db).get_balance(user).balance
                rewarded_ads_ssv_total.labels(status="duplicate").inc()
                return {"ok": True, "added": 0, "balance": balance, "duplicate": True}
            rewarded_ads_ssv_total.labels(status="invalid").inc()
            self._register_failure()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Event already processed")

        try:
            nonce_record = self.nonce_manager.consume(user_id, nonce)
        except AdsNonceError as exc:
            self._release_event_claim(event_id)
            rewarded_ads_ssv_total.labels(status="invalid").inc()
            self._register_failure()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

        if device_hash and device_hash != nonce_record.device_hash:
            rewarded_ads_ssv_total.labels(status="invalid").inc()
            self._register_failure()
            self._release_event_claim(event_id)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Device mismatch")

        if placement and placement != nonce_record.placement:
            rewarded_ads_ssv_total.labels(status="invalid").inc()
            self._register_failure()
            self._release_event_claim(event_id)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Placement mismatch")

        try:
            self.signature_verifier.verify(
                event_id=event_id,
                uid=str(user_id),
                nonce=nonce,
                amount=amount,
                duration=duration,
                device_hash=device_hash or nonce_record.device_hash,
                placement=placement or nonce_record.placement,
                signature=signature,
            )
        except HTTPException:
            self._release_event_claim(event_id)
            self._register_failure()
            rewarded_ads_ssv_total.labels(status="invalid").inc()
            raise

        now = datetime.now(timezone.utc)
        device_fingerprint = device_hash or nonce_record.device_hash
        limits = self._lock_limits(user_id, device_fingerprint, now.date())
        try:
            self._ensure_cap_available(limits, device_fingerprint)
            self._ensure_not_on_cooldown(limits, now)
            self._ensure_unique_nonce(user_id, nonce)
        except HTTPException:
            self._register_failure()
            self._release_event_claim(event_id)
            rewarded_ads_ssv_total.labels(status="invalid").inc()
            raise

        wallet_service = WalletService(self.db)
        reward = AdReward(
            user_id=user_id,
            network=network,
            event_id=event_id,
            nonce=nonce,
            reward_amount=amount,
            duration_sec=duration,
            placement=placement or nonce_record.placement,
            device_hash=device_fingerprint,
            meta={
                "ip": ip,
                "device_hash": device_fingerprint,
                "placement": placement or nonce_record.placement,
            },
        )

        try:
            with self.db.begin():
                self.db.add(reward)
                self.db.flush()
                self._increment_limits(limits, now)
                balance_info = wallet_service.adjust_balance(
                    user,
                    amount,
                    entry_type="ads.reward",
                    ref_id=reward.id,
                    meta={
                        "event_id": event_id,
                        "network": network,
                        "placement": placement or nonce_record.placement,
                    },
                )
        except Exception:
            self._release_event_claim(event_id)
            rewarded_ads_ssv_total.labels(status="error").inc()
            self._register_failure()
            raise

        self._persist_event_claim(event_id, reward.id)
        self._record_success_metrics(amount, duration, network, placement or nonce_record.placement)
        rewarded_ads_ssv_total.labels(status="success").inc()

        return {"ok": True, "added": amount, "balance": balance_info.balance}

    def _enforce_route(self, referer_path: str) -> None:
        if referer_path != "/earn":
            rewarded_ads_prepare_total.labels(status="invalid-route").inc()
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rewarded ads not available here")

    def _enforce_ip_policy(self, ip: str, asn: Optional[str]) -> None:
        blocked_asn = {item.lower() for item in self.settings.blocked_asn_list}
        if asn and asn.lower() in blocked_asn:
            rewarded_ads_prepare_total.labels(status="blocked").inc()
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Traffic blocked")

        for network in self.settings.blocked_ip_networks:
            try:
                if ipaddress.ip_address(ip) in network:
                    rewarded_ads_prepare_total.labels(status="blocked").inc()
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Traffic blocked")
            except ValueError:  # pragma: no cover - invalid IP
                continue

    def _verify_client_signature(self, *, user_id: UUID, ctx: PrepareContext, now: datetime) -> None:
        if not self.settings.client_signing_secret:
            return
        if not ctx.signature or not ctx.client_nonce or not ctx.timestamp:
            rewarded_ads_prepare_total.labels(status="bad-signature").inc()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing client signature")

        try:
            ts_int = int(ctx.timestamp)
        except ValueError as exc:
            rewarded_ads_prepare_total.labels(status="bad-signature").inc()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid timestamp") from exc

        delta = abs(now - datetime.fromtimestamp(ts_int, tz=timezone.utc))
        if delta > timedelta(minutes=5):
            rewarded_ads_prepare_total.labels(status="bad-signature").inc()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Signature timestamp too old")

        payload = f"{user_id}|{ctx.client_nonce}|{ctx.timestamp}|{ctx.placement}".encode("utf-8")
        expected = hmac.new(
            self.settings.client_signing_secret.encode("utf-8"),
            payload,
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(expected, ctx.signature):
            rewarded_ads_prepare_total.labels(status="bad-signature").inc()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid client signature")

    def _verify_recaptcha(self, ctx: PrepareContext, *, user_id: UUID) -> None:
        if not self.settings.recaptcha_project_id or not self.settings.recaptcha_api_key:
            if not self.settings.allow_missing_recaptcha:
                rewarded_ads_prepare_total.labels(status="recaptcha-missing").inc()
                raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="reCAPTCHA not configured")
            logger.warning("reCAPTCHA verification skipped because configuration is missing.")
            return
        if not ctx.recaptcha_token:
            rewarded_ads_prepare_total.labels(status="recaptcha-failed").inc()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="recaptcha_required")

        url = (
            f"https://recaptchaenterprise.googleapis.com/v1/projects/"
            f"{self.settings.recaptcha_project_id}/assessments?key={self.settings.recaptcha_api_key}"
        )
        payload = {
            "event": {
                "token": ctx.recaptcha_token,
                "siteKey": self.settings.recaptcha_site_key,
                "userAgent": ctx.user_agent,
                "userIpAddress": ctx.ip,
                "expectedAction": "ads_prepare",
            }
        }
        try:
            response = httpx.post(url, json=payload, timeout=5.0)
            response.raise_for_status()
        except Exception as exc:
            rewarded_ads_prepare_total.labels(status="recaptcha-error").inc()
            logger.exception("Failed to verify reCAPTCHA token")
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="recaptcha_verification_failed") from exc

        result = response.json()
        risk = result.get("riskAnalysis", {})
        score = float(risk.get("score") or 0.0)
        reasons = risk.get("reasons") or []
        if score < self.settings.recaptcha_min_score:
            rewarded_ads_prepare_total.labels(status="recaptcha-rejected").inc()
            logger.info("Recaptcha rejected user %s score %s reasons=%s", user_id, score, reasons)
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="recaptcha_failed")

    def _fetch_limits_snapshot(self, user_id: UUID, device_hash: str, day: date) -> LimitsSnapshot:
        stmt = (
            select(UserLimit)
            .where(UserLimit.user_id == user_id)
            .where(UserLimit.day == day)
            .where(UserLimit.device_hash.in_([self._user_limit_scope(), device_hash]))
        )
        limits = {record.device_hash: record for record in self.db.execute(stmt).scalars()}
        return LimitsSnapshot(
            user_limits=limits.get(self._user_limit_scope()),
            device_limits=limits.get(device_hash),
        )

    def _lock_limits(self, user_id: UUID, device_hash: str, day: date) -> LimitsSnapshot:
        stmt = (
            select(UserLimit)
            .where(UserLimit.user_id == user_id)
            .where(UserLimit.day == day)
            .where(UserLimit.device_hash.in_([self._user_limit_scope(), device_hash]))
            .with_for_update()
        )
        limits = {record.device_hash: record for record in self.db.execute(stmt).scalars()}

        user_limits = limits.get(self._user_limit_scope())
        if user_limits is None:
            user_limits = UserLimit(
                user_id=user_id,
                device_hash=self._user_limit_scope(),
                day=day,
                rewards=0,
                device_rewards=0,
            )
            self.db.add(user_limits)

        device_limits = limits.get(device_hash)
        if device_limits is None:
            device_limits = UserLimit(
                user_id=user_id,
                device_hash=device_hash,
                day=day,
                rewards=0,
                device_rewards=0,
            )
            self.db.add(device_limits)

        return LimitsSnapshot(user_limits=user_limits, device_limits=device_limits)

    def _ensure_not_on_cooldown(self, limits: LimitsSnapshot, now: datetime) -> None:
        last_reward_at = limits.last_reward_at
        if not last_reward_at:
            return
        delta = (now - last_reward_at).total_seconds()
        if delta < self.settings.reward_min_interval:
            rewarded_ads_prepare_total.labels(status="cooldown").inc()
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Cooldown active")

    def _ensure_cap_available(self, limits: LimitsSnapshot, device_hash: str) -> None:
        effective_cap = self._get_effective_daily_cap()
        if limits.user_limits and limits.user_limits.rewards >= effective_cap:
            rewarded_ads_prepare_total.labels(status="cap").inc()
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Daily cap reached")
        if limits.device_limits and limits.device_limits.device_rewards >= self.settings.rewards_per_device:
            rewarded_ads_prepare_total.labels(status="cap").inc()
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Device cap reached")

    def _increment_limits(self, limits: LimitsSnapshot, now: datetime) -> None:
        if limits.user_limits:
            limits.user_limits.rewards = (limits.user_limits.rewards or 0) + 1
            limits.user_limits.last_reward_at = now
        if limits.device_limits:
            limits.device_limits.device_rewards = (limits.device_limits.device_rewards or 0) + 1
            limits.device_limits.last_reward_at = now

    def _ensure_unique_nonce(self, user_id: UUID, nonce: str) -> None:
        stmt = (
            select(AdReward)
            .where(AdReward.user_id == user_id)
            .where(AdReward.nonce == nonce)
        )
        existing = self.db.execute(stmt).scalar_one_or_none()
        if existing:
            rewarded_ads_ssv_total.labels(status="duplicate").inc()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Nonce already consumed")

    def _claim_event(self, event_id: str) -> bool:
        if self.redis is None:
            return True
        key = f"{EVENT_REDIS_PREFIX}:{event_id}"
        try:
            return bool(self.redis.set(key, "processing", nx=True, ex=86400))
        except Exception:  # pragma: no cover - fallback
            return True

    def _release_event_claim(self, event_id: str) -> None:
        if self.redis is None:
            return
        key = f"{EVENT_REDIS_PREFIX}:{event_id}"
        try:
            self.redis.delete(key)
        except Exception:  # pragma: no cover
            pass

    def _persist_event_claim(self, event_id: str, reward_id: UUID) -> None:
        if self.redis is None:
            return
        key = f"{EVENT_REDIS_PREFIX}:{event_id}"
        try:
            self.redis.set(key, str(reward_id), ex=86400)
        except Exception:  # pragma: no cover
            pass

    def _build_ad_tag_url(self, user_id: UUID, nonce: str, placement: str, device_hash: str) -> str:
        from urllib.parse import urlencode, urlparse, urlunparse, parse_qsl

        base_url = self.settings.ad_tag_base.rstrip("?")

        cust_params = {
            "uid": str(user_id),
            "nonce": nonce,
            "placement": placement,
            "device": device_hash,
        }
        if self.settings.price_floor is not None:
            cust_params["floor"] = str(self.settings.price_floor)

        query_params = dict(parse_qsl(urlparse(base_url).query))
        query_params["cust_params"] = urlencode(cust_params)
        query_params["reward_amount"] = str(self.settings.reward_amount)
        parsed = urlparse(base_url)
        rebuilt = parsed._replace(query=urlencode(query_params))
        return urlunparse(rebuilt)

    def _record_success_metrics(self, amount: int, duration: int, network: str, placement: str | None) -> None:
        rewarded_ads_reward_amount.labels(network=network, placement=placement or "unknown").inc(amount)
        rewarded_ads_duration_seconds.observe(duration)
        self._register_stat(success=True)

    def _register_failure(self) -> None:
        self._register_stat(success=False)

    def _register_stat(self, *, success: bool) -> None:
        if self.redis is None:
            return
        key = SUCCESS_STAT_REDIS_PREFIX if success else FAIL_STAT_REDIS_PREFIX
        try:
            count = self.redis.incr(key)
            if count == 1:
                self.redis.expire(key, 1800)
        except Exception:  # pragma: no cover
            return
        self._recompute_failure_ratio()

    def _recompute_failure_ratio(self) -> None:
        if self.redis is None:
            return
        try:
            success = int(self.redis.get(SUCCESS_STAT_REDIS_PREFIX) or 0)
            fail = int(self.redis.get(FAIL_STAT_REDIS_PREFIX) or 0)
        except Exception:  # pragma: no cover
            return
        total = success + fail
        ratio = (fail / total) if total else 0.0
        rewarded_ads_failure_ratio.set(ratio)
        base_cap = self.settings.rewards_per_day
        cap = base_cap
        if ratio > self.settings.ssv_failure_threshold:
            cap = max(self.settings.adaptive_cap_floor, base_cap // 2)
        try:
            self.redis.set(CAP_REDIS_KEY, cap, ex=1800)
        except Exception:  # pragma: no cover
            pass
        rewarded_ads_daily_cap.set(cap)

    def _get_effective_daily_cap(self) -> int:
        base_cap = self.settings.rewards_per_day
        if self.redis is None:
            rewarded_ads_daily_cap.set(base_cap)
            return base_cap
        try:
            value = self.redis.get(CAP_REDIS_KEY)
        except Exception:  # pragma: no cover
            rewarded_ads_daily_cap.set(base_cap)
            return base_cap
        if value is None:
            rewarded_ads_daily_cap.set(base_cap)
            return base_cap
        try:
            cap = max(int(value), self.settings.adaptive_cap_floor)
        except ValueError:
            cap = base_cap
        rewarded_ads_daily_cap.set(cap)
        return cap

    def _user_limit_scope(self) -> str:
        return "__user__"

    def _get_reward_by_event(self, event_id: str) -> Optional[AdReward]:
        stmt = select(AdReward).where(AdReward.event_id == event_id)
        return self.db.execute(stmt).scalar_one_or_none()


def compute_device_hash(
    *,
    secret: str,
    ip_address: str,
    user_agent: str,
    client_hints: Dict[str, str],
) -> str:
    subnet = _ip_subnet(ip_address)
    hints = "|".join(f"{key}:{value}" for key, value in sorted(client_hints.items()))
    payload = f"{subnet}|{user_agent}|{hints}".encode("utf-8")
    digest = hashlib.sha256(secret.encode("utf-8") + payload).hexdigest()
    return digest


def _ip_subnet(ip_raw: str) -> str:
    try:
        ip_obj = ipaddress.ip_address(ip_raw)
    except ValueError:
        return ip_raw

    if isinstance(ip_obj, ipaddress.IPv4Address):
        network = ipaddress.IPv4Network(f"{ip_raw}/24", strict=False)
        return str(network.network_address)
    network = ipaddress.IPv6Network(f"{ip_raw}/64", strict=False)
    return str(network.network_address)


__all__ = [
    "AdsService",
    "AdsNonceManager",
    "AdsNonceError",
    "compute_device_hash",
    "PrepareContext",
]
