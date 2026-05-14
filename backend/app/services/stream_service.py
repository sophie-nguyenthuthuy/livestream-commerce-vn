from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.stream import Stream, StreamMinute
from app.schemas.stream import ConversionFunnel, StreamEvent


def _floor_minute(ts: datetime) -> datetime:
    return ts.astimezone(UTC).replace(second=0, microsecond=0)


async def ingest_events(
    session: AsyncSession,
    stream_id: UUID,
    events: list[StreamEvent],
) -> int:
    """Upsert per-minute rollups. Concurrent-viewer fields take MAX, others SUM."""
    if not events:
        return 0

    # Aggregate in memory first to keep round-trips bounded.
    buckets: dict[datetime, dict[str, Any]] = {}
    for ev in events:
        bucket = _floor_minute(ev.occurred_at)
        agg = buckets.setdefault(
            bucket,
            {
                "concurrent_viewers": 0,
                "new_viewers": 0,
                "comments": 0,
                "likes": 0,
                "shares": 0,
                "product_clicks": 0,
                "add_to_carts": 0,
                "orders": 0,
                "gmv_vnd": Decimal("0"),
                "featured_product_id": None,
            },
        )
        agg["concurrent_viewers"] = max(agg["concurrent_viewers"], ev.concurrent_viewers)
        agg["new_viewers"] += ev.new_viewers
        agg["comments"] += ev.comments
        agg["likes"] += ev.likes
        agg["shares"] += ev.shares
        agg["product_clicks"] += ev.product_clicks
        agg["add_to_carts"] += ev.add_to_carts
        agg["orders"] += ev.orders
        agg["gmv_vnd"] += ev.gmv_vnd
        if ev.featured_product_id is not None:
            agg["featured_product_id"] = ev.featured_product_id

    rows = [
        {"stream_id": stream_id, "bucket_ts": bucket, **agg} for bucket, agg in buckets.items()
    ]

    stmt = pg_insert(StreamMinute).values(rows)
    stmt = stmt.on_conflict_do_update(
        index_elements=["stream_id", "bucket_ts"],
        set_={
            "concurrent_viewers": pg_insert(StreamMinute).excluded.concurrent_viewers,
            "new_viewers": StreamMinute.new_viewers + pg_insert(StreamMinute).excluded.new_viewers,
            "comments": StreamMinute.comments + pg_insert(StreamMinute).excluded.comments,
            "likes": StreamMinute.likes + pg_insert(StreamMinute).excluded.likes,
            "shares": StreamMinute.shares + pg_insert(StreamMinute).excluded.shares,
            "product_clicks": (
                StreamMinute.product_clicks + pg_insert(StreamMinute).excluded.product_clicks
            ),
            "add_to_carts": (
                StreamMinute.add_to_carts + pg_insert(StreamMinute).excluded.add_to_carts
            ),
            "orders": StreamMinute.orders + pg_insert(StreamMinute).excluded.orders,
            "gmv_vnd": StreamMinute.gmv_vnd + pg_insert(StreamMinute).excluded.gmv_vnd,
            "featured_product_id": pg_insert(StreamMinute).excluded.featured_product_id,
        },
    )
    await session.execute(stmt)
    await session.commit()
    return len(rows)


async def compute_funnel(session: AsyncSession, stream_id: UUID) -> ConversionFunnel:
    q = select(StreamMinute).where(StreamMinute.stream_id == stream_id)
    rows = (await session.execute(q)).scalars().all()

    viewers = sum(r.new_viewers for r in rows)
    clicks = sum(r.product_clicks for r in rows)
    carts = sum(r.add_to_carts for r in rows)
    orders = sum(r.orders for r in rows)
    gmv = sum((r.gmv_vnd for r in rows), Decimal("0"))

    return ConversionFunnel(
        viewers=viewers,
        product_clicks=clicks,
        add_to_carts=carts,
        orders=orders,
        click_through_rate=(clicks / viewers) if viewers else 0.0,
        cart_rate=(carts / clicks) if clicks else 0.0,
        order_rate=(orders / carts) if carts else 0.0,
        gmv_vnd=gmv,
        aov_vnd=(gmv / orders) if orders else Decimal("0"),
    )


async def get_stream(session: AsyncSession, stream_id: UUID) -> Stream | None:
    return await session.get(Stream, stream_id)
