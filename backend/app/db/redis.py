from __future__ import annotations

from typing import Any

from redis.asyncio import Redis, from_url

from app.core.config import get_settings

_redis: Redis[Any] | None = None


async def get_redis() -> Redis[Any]:
    global _redis
    if _redis is None:
        settings = get_settings()
        _redis = from_url(str(settings.redis_url), encoding="utf-8", decode_responses=True)
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.close()
        _redis = None
