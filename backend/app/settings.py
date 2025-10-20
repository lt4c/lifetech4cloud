import ipaddress
import re
from functools import lru_cache
from typing import List, Set
from urllib.parse import urlparse

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    discord_client_id: str = Field(..., alias="DISCORD_CLIENT_ID")
    discord_client_secret: str = Field(..., alias="DISCORD_CLIENT_SECRET")
    discord_redirect_uri: AnyHttpUrl = Field(..., alias="DISCORD_REDIRECT_URI")
    secret_key: str = Field(..., alias="SECRET_KEY")
    database_url: str = Field(..., alias="DATABASE_URL")
    base_url: AnyHttpUrl = Field(..., alias="BASE_URL")
    allowed_origins: str = Field("*", alias="ALLOWED_ORIGINS")
    cookie_secure: bool = Field(False, alias="COOKIE_SECURE")
    session_cookie_name: str = Field("session", alias="SESSION_COOKIE_NAME")
    encryption_key: str = Field(..., alias="ENCRYPTION_KEY")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    hface_gpt_base_url: AnyHttpUrl | None = Field(default=None, alias="HFACE_GPT_BASE_URL")
    hface_gpt_model: str = Field("GPT-OSS-120B", alias="HFACE_GPT_MODEL")
    redis_url: str | None = Field(default=None, alias="REDIS_URL")
    feature_flags: str = Field("", alias="FEATURE_FLAGS")
    frontend_redirect_url: str | None = Field(default=None, alias="FRONTEND_REDIRECT_URL")
    canary_percent: int = Field(5, alias="CANARY_PERCENT", ge=0, le=100)
    reward_amount: int = Field(5, alias="REWARD_AMOUNT", ge=1)
    required_duration: int = Field(30, alias="REQUIRED_DURATION", ge=1)
    reward_min_interval: int = Field(30, alias="MIN_INTERVAL", ge=1)
    rewards_per_day: int = Field(40, alias="RWD_PER_DAY", ge=1)
    rewards_per_device: int = Field(60, alias="RWD_PER_DEVICE", ge=1)
    adaptive_cap_floor: int = Field(20, alias="RWD_PER_DAY_MIN", ge=1)
    ssv_failure_threshold: float = Field(0.2, alias="SSV_FAIL_THRESHOLD", ge=0.0, le=1.0)
    ad_tag_base: str = Field("https://example.com/gam", alias="AD_TAG_BASE")
    price_floor: float | None = Field(default=None, alias="PRICE_FLOOR")
    ssv_secret: str | None = Field(default=None, alias="SSV_SECRET")
    ssv_public_key_path: str | None = Field(default=None, alias="PUBLIC_KEY_PATH")
    client_signing_secret: str | None = Field(default=None, alias="CLIENT_SIGNING_SECRET")
    recaptcha_project_id: str | None = Field(default=None, alias="RECAPTCHA_PROJECT_ID")
    recaptcha_site_key: str | None = Field(default=None, alias="RECAPTCHA_SITE_KEY")
    recaptcha_api_key: str | None = Field(default=None, alias="RECAPTCHA_API_KEY")
    recaptcha_min_score: float = Field(0.5, alias="RECAPTCHA_MIN_SCORE", ge=0.0, le=1.0)
    allow_missing_recaptcha: bool = Field(False, alias="RECAPTCHA_ALLOW_MISSING")
    blocked_asn: str = Field("", alias="ADS_BLOCKED_ASN")
    blocked_ips: str = Field("", alias="ADS_BLOCKED_IPS")
    ads_allowed_placements: str = Field("earn,daily,boost,test", alias="ADS_ALLOWED_PLACEMENTS")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @staticmethod
    def _origin_from_url(value: str | AnyHttpUrl | None) -> str | None:
        if not value:
            return None
        try:
            parsed = urlparse(str(value).strip())
        except ValueError:
            return None
        if not parsed.scheme or not parsed.hostname:
            return None
        origin = f"{parsed.scheme}://{parsed.hostname}"
        if parsed.port:
            origin = f"{origin}:{parsed.port}"
        return origin

    @classmethod
    def _origin_variants(cls, value: str | AnyHttpUrl | None) -> list[str]:
        origin = cls._origin_from_url(value)
        if not origin:
            return []
        variants = [origin]
        parsed = urlparse(origin)
        if parsed.scheme == "http" and parsed.port in (None, 80):
            https_origin = f"https://{parsed.hostname}"
            if https_origin not in variants:
                variants.append(https_origin)
        return variants

    @property
    def allowed_origins_list(self) -> List[str]:
        raw = (self.allowed_origins or "").strip()
        if raw == "*":
            return ["*"]

        origins: List[str] = []

        def _add_origin(candidate: str | None) -> None:
            if not candidate:
                return
            for item in self._origin_variants(candidate):
                if item not in origins:
                    origins.append(item)

        if raw:
            for entry in re.split(r"[\s,]+", raw):
                candidate = entry.strip()
                if not candidate:
                    continue
                parsed = self._origin_from_url(candidate)
                _add_origin(parsed or candidate)

        fallback = self._origin_from_url(self.frontend_redirect_url)
        _add_origin(fallback)

        return origins

    @property
    def discord_scopes(self) -> str:
        return "identify email"

    @property
    def feature_flags_list(self) -> List[str]:
        raw = self.feature_flags.strip()
        if not raw:
            return []
        return [flag.strip() for flag in raw.split(",") if flag.strip()]

    @property
    def feature_flags_set(self) -> Set[str]:
        return {flag.lower() for flag in self.feature_flags_list}

    def is_feature_enabled(self, flag: str) -> bool:
        return flag.lower() in self.feature_flags_set

    @property
    def frontend_redirect_target(self) -> str:
        target = (self.frontend_redirect_url or "").strip()
        if not target:
            return "/"
        return target

    @property
    def blocked_asn_list(self) -> List[str]:
        raw = (self.blocked_asn or "").strip()
        if not raw:
            return []
        return [item.strip() for item in raw.split(",") if item.strip()]

    @property
    def blocked_ip_networks(self) -> List[ipaddress._BaseNetwork]:
        value = (self.blocked_ips or "").strip()
        networks: List[ipaddress._BaseNetwork] = []
        if not value:
            return networks
        for entry in re.split(r"[\s,]+", value):
            candidate = entry.strip()
            if not candidate:
                continue
            try:
                networks.append(ipaddress.ip_network(candidate, strict=False))
            except ValueError:
                continue
        return networks

    @property
    def allowed_placements(self) -> List[str]:
        raw = (self.ads_allowed_placements or "").strip()
        if not raw:
            return ["earn"]
        return [item.strip() for item in raw.split(",") if item.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
