from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.api.deps import DbSession
from app.models.stream import Stream, StreamMinute, StreamStatus
from app.schemas.stream import (
    ConversionFunnel,
    StreamCreate,
    StreamEventBatch,
    StreamMinuteRead,
    StreamRead,
)
from app.services.stream_service import compute_funnel, get_stream, ingest_events

router = APIRouter()


@router.post("", response_model=StreamRead, status_code=status.HTTP_201_CREATED)
async def create_stream(payload: StreamCreate, db: DbSession) -> Stream:
    stream = Stream(**payload.model_dump())
    if stream.started_at is not None:
        stream.status = StreamStatus.LIVE
    db.add(stream)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "stream already exists for this platform/platform_stream_id",
        ) from exc
    await db.refresh(stream)
    return stream


@router.get("/{stream_id}", response_model=StreamRead)
async def read_stream(stream_id: UUID, db: DbSession) -> Stream:
    stream = await get_stream(db, stream_id)
    if stream is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "stream not found")
    return stream


@router.post("/{stream_id}/end", response_model=StreamRead)
async def end_stream(stream_id: UUID, db: DbSession) -> Stream:
    stream = await get_stream(db, stream_id)
    if stream is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "stream not found")
    if stream.status == StreamStatus.ENDED:
        return stream
    stream.status = StreamStatus.ENDED
    stream.ended_at = datetime.now(UTC)

    rows = (
        (
            await db.execute(
                select(StreamMinute).where(StreamMinute.stream_id == stream_id)
            )
        )
        .scalars()
        .all()
    )
    stream.total_viewers = sum(r.new_viewers for r in rows)
    stream.peak_concurrent_viewers = max((r.concurrent_viewers for r in rows), default=0)
    stream.total_orders = sum(r.orders for r in rows)
    stream.gmv_vnd = sum((r.gmv_vnd for r in rows), start=Decimal("0"))
    await db.commit()
    await db.refresh(stream)
    return stream


@router.post("/{stream_id}/events", status_code=status.HTTP_202_ACCEPTED)
async def ingest_stream_events(
    stream_id: UUID, batch: StreamEventBatch, db: DbSession
) -> dict[str, int]:
    if (await get_stream(db, stream_id)) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "stream not found")
    written = await ingest_events(db, stream_id, batch.events)
    return {"buckets_upserted": written, "events_received": len(batch.events)}


@router.get("/{stream_id}/minutes", response_model=list[StreamMinuteRead])
async def list_minutes(
    stream_id: UUID,
    db: DbSession,
    limit: int = Query(default=240, ge=1, le=1440),
) -> list[StreamMinute]:
    if (await get_stream(db, stream_id)) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "stream not found")
    q = (
        select(StreamMinute)
        .where(StreamMinute.stream_id == stream_id)
        .order_by(StreamMinute.bucket_ts.asc())
        .limit(limit)
    )
    return list((await db.execute(q)).scalars().all())


@router.get("/{stream_id}/conversion", response_model=ConversionFunnel)
async def get_conversion(stream_id: UUID, db: DbSession) -> ConversionFunnel:
    if (await get_stream(db, stream_id)) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "stream not found")
    return await compute_funnel(db, stream_id)
