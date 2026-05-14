from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_env: Literal["development", "staging", "production", "test"] = "development"
    app_secret_key: str = Field(min_length=16)
    api_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:3000"

    # Database
    database_url: PostgresDsn

    # Redis
    redis_url: RedisDsn

    # Object storage
    s3_endpoint: str
    s3_access_key: str
    s3_secret_key: str
    s3_bucket: str = "thumbnails"
    s3_region: str = "ap-southeast-1"

    # AI
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    ai_primary_provider: Literal["anthropic", "openai"] = "anthropic"
    ai_model_anthropic: str = "claude-sonnet-4-6"
    ai_model_openai: str = "gpt-4o"

    # TikTok Shop
    tiktok_shop_app_key: str | None = None
    tiktok_shop_app_secret: str | None = None
    tiktok_webhook_secret: str | None = None

    # Observability
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    sentry_dsn: str | None = None

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
