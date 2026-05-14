from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import Field

from app.models.stream import Platform, StreamStatus
from app.schemas.common import APIModel


class StreamCreate(APIModel):
    platform: Platform = Platform.TIKTOK_SHOP
    platform_stream_id: str = Field(min_length=1, max_length=64)
    host_handle: str = Field(min_length=1, max_length=128)
    title: str = Field(min_length=1, max_length=255)
    started_at: datetime | None = None


class StreamRead(APIModel):
    id: UUID
    platform: Platform
    platform_stream_id: str
    host_handle: str
    title: str
    status: StreamStatus
    started_at: datetime | None
    ended_at: datetime | None
    total_viewers: int
    peak_concurrent_viewers: int
    total_orders: int
    gmv_vnd: Decimal


class StreamEvent(APIModel):
    """A single sample of stream state. Sender batches these and POSTs."""

    occurred_at: datetime
    concurrent_viewers: int = Field(ge=0)
    new_viewers: int = Field(ge=0, default=0)
    comments: int = Field(ge=0, default=0)
    likes: int = Field(ge=0, default=0)
    shares: int = Field(ge=0, default=0)
    product_clicks: int = Field(ge=0, default=0)
    add_to_carts: int = Field(ge=0, default=0)
    orders: int = Field(ge=0, default=0)
    gmv_vnd: Decimal = Field(ge=Decimal("0"), default=Decimal("0"))
    featured_product_id: UUID | None = None


class StreamEventBatch(APIModel):
    events: list[StreamEvent] = Field(min_length=1, max_length=1000)


class StreamMinuteRead(APIModel):
    bucket_ts: datetime
    concurrent_viewers: int
    new_viewers: int
    comments: int
    likes: int
    product_clicks: int
    add_to_carts: int
    orders: int
    gmv_vnd: Decimal
    featured_product_id: UUID | None

    @property
    def cvr(self) -> float:
        return self.orders / self.concurrent_viewers if self.concurrent_viewers else 0.0


class ConversionFunnel(APIModel):
    viewers: int
    product_clicks: int
    add_to_carts: int
    orders: int
    click_through_rate: float
    cart_rate: float
    order_rate: float
    gmv_vnd: Decimal
    aov_vnd: Decimal
