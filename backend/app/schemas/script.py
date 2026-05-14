from __future__ import annotations

from uuid import UUID

from pydantic import Field

from app.models.script import Dialect, ScriptIntent
from app.schemas.common import APIModel


class ScriptGenerateRequest(APIModel):
    product_id: UUID | None = None
    product_name: str | None = Field(default=None, max_length=255)
    product_category: str | None = Field(default=None, max_length=64)
    price_band: str | None = Field(
        default=None,
        description="e.g. 'under-200k', '200-500k', 'premium-1m-plus'",
    )
    dialect: Dialect = Dialect.SOUTH
    intent: ScriptIntent = ScriptIntent.HOOK
    audience_persona: str | None = Field(
        default=None,
        description="Free-text persona, e.g. 'mom 28-40 shopping for skincare'",
    )
    target_duration_sec: int = Field(default=30, ge=10, le=180)
    n_variants: int = Field(default=3, ge=1, le=5)


class ScriptVariant(APIModel):
    title: str
    body: str
    estimated_duration_sec: int
    tags: list[str] = []


class ScriptGenerateResponse(APIModel):
    dialect: Dialect
    intent: ScriptIntent
    model: str
    variants: list[ScriptVariant]


class ScriptRead(APIModel):
    id: UUID
    product_id: UUID | None
    dialect: Dialect
    intent: ScriptIntent
    title: str
    body: str
    speech_duration_sec: int
    tags: list[str]
    model: str | None
    use_count: int
    upvotes: int


class ScriptSave(APIModel):
    product_id: UUID | None = None
    dialect: Dialect
    intent: ScriptIntent
    title: str = Field(min_length=1, max_length=255)
    body: str = Field(min_length=1)
    speech_duration_sec: int = Field(ge=0, le=600)
    tags: list[str] = []
    model: str | None = None
