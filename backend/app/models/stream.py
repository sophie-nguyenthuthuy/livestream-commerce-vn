from __future__ import annotations

import enum
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


class Platform(str, enum.Enum):
    TIKTOK_SHOP = "TIKTOK_SHOP"
    SHOPEE_LIVE = "SHOPEE_LIVE"
    LAZADA_LIVE = "LAZADA_LIVE"


class StreamStatus(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    LIVE = "LIVE"
    ENDED = "ENDED"


class Stream(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "streams"

    platform: Mapped[Platform] = mapped_column(Enum(Platform), default=Platform.TIKTOK_SHOP)
    platform_stream_id: Mapped[str] = mapped_column(String(64), index=True)
    host_handle: Mapped[str] = mapped_column(String(128), index=True)
    title: Mapped[str] = mapped_column(String(255))
    status: Mapped[StreamStatus] = mapped_column(
        Enum(StreamStatus), default=StreamStatus.SCHEDULED
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Rollups updated at stream end
    total_viewers: Mapped[int] = mapped_column(BigInteger, default=0)
    peak_concurrent_viewers: Mapped[int] = mapped_column(Integer, default=0)
    total_orders: Mapped[int] = mapped_column(Integer, default=0)
    gmv_vnd: Mapped[Decimal] = mapped_column(Numeric(16, 2), default=Decimal("0"))

    minutes: Mapped[list[StreamMinute]] = relationship(
        back_populates="stream", cascade="all, delete-orphan"
    )
    products: Mapped[list[StreamProduct]] = relationship(
        back_populates="stream", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("platform", "platform_stream_id", name="uq_streams_platform_id"),
        Index("ix_streams_host_started", "host_handle", "started_at"),
    )


class StreamMinute(Base):
    """Per-minute time-series bucket. Backed by a TimescaleDB hypertable."""

    __tablename__ = "stream_minutes"

    stream_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("streams.id", ondelete="CASCADE"), primary_key=True
    )
    bucket_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)

    concurrent_viewers: Mapped[int] = mapped_column(Integer, default=0)
    new_viewers: Mapped[int] = mapped_column(Integer, default=0)
    comments: Mapped[int] = mapped_column(Integer, default=0)
    likes: Mapped[int] = mapped_column(Integer, default=0)
    shares: Mapped[int] = mapped_column(Integer, default=0)
    product_clicks: Mapped[int] = mapped_column(Integer, default=0)
    add_to_carts: Mapped[int] = mapped_column(Integer, default=0)
    orders: Mapped[int] = mapped_column(Integer, default=0)
    gmv_vnd: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))

    # Featured product at this minute (used to attribute conversion to script segments)
    featured_product_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("products.id", ondelete="SET NULL"), nullable=True
    )

    stream: Mapped[Stream] = relationship(back_populates="minutes")

    __table_args__ = (
        Index("ix_stream_minutes_bucket", "bucket_ts"),
    )


class StreamProduct(Base):
    __tablename__ = "stream_products"

    stream_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("streams.id", ondelete="CASCADE"), primary_key=True
    )
    product_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), primary_key=True
    )
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    featured_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    featured_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    stream: Mapped[Stream] = relationship(back_populates="products")
