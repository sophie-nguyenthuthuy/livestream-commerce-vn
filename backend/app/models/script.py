from __future__ import annotations

import enum
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDMixin


class Dialect(str, enum.Enum):
    NORTH = "NORTH"  # Hà Nội — formal "ạ", "vâng", neutral lexicon
    SOUTH = "SOUTH"  # Sài Gòn — informal "nha", "dạ", warmer lexicon
    NEUTRAL = "NEUTRAL"


class ScriptIntent(str, enum.Enum):
    HOOK = "HOOK"  # opening, attention-grabbing
    PITCH = "PITCH"  # product features
    SOCIAL_PROOF = "SOCIAL_PROOF"  # reviews, testimonials
    OBJECTION = "OBJECTION"  # handle hesitation
    URGENCY = "URGENCY"  # flash sale, last units
    CLOSE = "CLOSE"  # call to action


class ScriptTemplate(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "script_templates"

    product_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("products.id", ondelete="SET NULL"), nullable=True
    )
    dialect: Mapped[Dialect] = mapped_column(Enum(Dialect))
    intent: Mapped[ScriptIntent] = mapped_column(Enum(ScriptIntent))

    title: Mapped[str] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(Text)
    speech_duration_sec: Mapped[int] = mapped_column(Integer, default=0)

    # Tags help with retrieval/filtering: ["under-200k", "skincare", "gen-z"]
    tags: Mapped[list[str]] = mapped_column(JSONB, default=list)

    # AI provenance
    model: Mapped[str | None] = mapped_column(String(64), nullable=True)
    prompt_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Performance tracking — host marks scripts that converted well
    use_count: Mapped[int] = mapped_column(Integer, default=0)
    upvotes: Mapped[int] = mapped_column(Integer, default=0)

    __table_args__ = (
        Index("ix_script_templates_filter", "dialect", "intent"),
        Index("ix_script_templates_product", "product_id", "intent"),
    )
