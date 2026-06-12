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

    # AI — self-hosted OSS LLM via OpenAI-compatible endpoint.
    # Defaults: Ollama on localhost serving Qwen 2.5. For GPU production
    # swap to vLLM/SGLang at the same base_url. No managed-API providers.
    llm_base_url: str = "http://localhost:11434/v1"
    llm_api_key: str | None = None
    # 7b is the CPU/laptop dev default; production GPU should set
    # LLM_MODEL=qwen2.5:32b-instruct in the deploy env.
    llm_model: str = "qwen2.5:7b-instruct"

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
    return Settings()
