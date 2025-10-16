from functools import lru_cache

from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AdminRateLimit(BaseModel):
    requests: int = 100
    window_seconds: int = 60

    @validator("requests", "window_seconds")
    def validate_positive(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("Rate limit values must be positive integers.")
        return value


class AdminSettings(BaseSettings):
    enabled: bool = Field(False, alias="ADMIN_ENABLED")
    prefix: str = Field("/admin", alias="ADMIN_PREFIX")
    api_prefix: str = Field("/api/v1/admin", alias="ADMIN_API_PREFIX")
    default_password: str | None = Field(None, alias="ADMIN_DEFAULT_PASSWORD")
    rate_limit_requests: int = Field(100, alias="ADMIN_RATE_LIMIT_REQUESTS")
    rate_limit_window_seconds: int = Field(60, alias="ADMIN_RATE_LIMIT_WINDOW_SECONDS")
    redis_url: str | None = Field(None, alias="ADMIN_REDIS_URL")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @validator("prefix", "api_prefix")
    def ensure_leading_slash(cls, value: str) -> str:
        if not value.startswith("/"):
            value = "/" + value
        return value.rstrip("/") or "/"

    @property
    def rate_limit(self) -> AdminRateLimit:
        return AdminRateLimit(
            requests=self.rate_limit_requests,
            window_seconds=self.rate_limit_window_seconds,
        )


@lru_cache(maxsize=1)
def get_admin_settings() -> AdminSettings:
    return AdminSettings()
