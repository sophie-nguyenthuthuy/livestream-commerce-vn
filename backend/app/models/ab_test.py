from __future__ import annotations

import enum
from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


class ABTestStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    DECIDED = "DECIDED"
    ARCHIVED = "ARCHIVED"


class ABTestEventType(str, enum.Enum):
    IMPRESSION = "IMPRESSION"
    CLICK = "CLICK"


class ABTest(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "ab_tests"

    name: Mapped[str] = mapped_column(String(255))
    hypothesis: Mapped[str | None] = mapped_column(Text, nullable=True)
    product_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("products.id", ondelete="SET NULL"), nullable=True
    )

    status: Mapped[ABTestStatus] = mapped_column(Enum(ABTestStatus), default=ABTestStatus.DRAFT)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Guardrails
    min_impressions_per_variant: Mapped[int] = mapped_column(Integer, default=1000)
    confidence_target: Mapped[float] = mapped_column(default=0.95)

    winner_variant_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("ab_test_variants.id", ondelete="SET NULL", use_alter=True),
        nullable=True,
    )

    variants: Mapped[list[ABTestVariant]] = relationship(
        back_populates="test",
        cascade="all, delete-orphan",
        foreign_keys="ABTestVariant.test_id",
    )


class ABTestVariant(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "ab_test_variants"

    test_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("ab_tests.id", ondelete="CASCADE"), index=True
    )
    label: Mapped[str] = mapped_column(String(64))  # "A", "B", "control"
    thumbnail_url: Mapped[str] = mapped_column(String(512))
    weight: Mapped[int] = mapped_column(Integer, default=50)  # traffic split %

    test: Mapped[ABTest] = relationship(back_populates="variants", foreign_keys=[test_id])

    __table_args__ = (
        UniqueConstraint("test_id", "label", name="uq_ab_variant_label"),
        CheckConstraint("weight >= 0 AND weight <= 100", name="ck_ab_variant_weight"),
    )


class ABTestEvent(Base):
    """Append-only event store. Aggregated for results computation."""

    __tablename__ = "ab_test_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    variant_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("ab_test_variants.id", ondelete="CASCADE"),
        index=True,
    )
    event_type: Mapped[ABTestEventType] = mapped_column(Enum(ABTestEventType), index=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    session_hash: Mapped[str] = mapped_column(String(64))  # dedupe key per viewer session

    __table_args__ = (
        Index("ix_ab_events_variant_type_time", "variant_id", "event_type", "occurred_at"),
    )
