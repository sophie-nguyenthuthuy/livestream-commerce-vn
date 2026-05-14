from __future__ import annotations

import hashlib
import hmac
import secrets

from app.core.config import get_settings


def verify_webhook_signature(payload: bytes, provided_signature: str) -> bool:
    """Validate TikTok Shop webhook signature with HMAC-SHA256, constant-time compare."""
    settings = get_settings()
    if not settings.tiktok_webhook_secret:
        return False
    expected = hmac.new(
        settings.tiktok_webhook_secret.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, provided_signature)


def generate_api_key() -> str:
    return f"lvc_{secrets.token_urlsafe(32)}"
