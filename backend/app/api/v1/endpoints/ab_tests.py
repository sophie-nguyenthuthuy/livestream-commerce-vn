from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import DbSession
from app.models.ab_test import (
    ABTest,
    ABTestEvent,
    ABTestEventType,
    ABTestStatus,
    ABTestVariant,
)
from app.schemas.ab_test import (
    ABEventBatch,
    ABTestCreate,
    ABTestRead,
    ABTestResults,
    ABVariantResult,
)
from app.services.ab_test_service import VariantStats, evaluate

router = APIRouter()


@router.post("", response_model=ABTestRead, status_code=status.HTTP_201_CREATED)
async def create_test(payload: ABTestCreate, db: DbSession) -> ABTest:
    test = ABTest(
        name=payload.name,
        hypothesis=payload.hypothesis,
        product_id=payload.product_id,
        min_impressions_per_variant=payload.min_impressions_per_variant,
        confidence_target=payload.confidence_target,
    )
    test.variants = [
        ABTestVariant(label=v.label, thumbnail_url=v.thumbnail_url, weight=v.weight)
        for v in payload.variants
    ]
    db.add(test)
    await db.commit()
    await db.refresh(test, attribute_names=["variants"])
    return test


@router.post("/{test_id}/start", response_model=ABTestRead)
async def start_test(test_id: UUID, db: DbSession) -> ABTest:
    test = await _get_test(db, test_id)
    if test.status not in (ABTestStatus.DRAFT, ABTestStatus.PAUSED):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"cannot start test in status {test.status.value}",
        )
    test.status = ABTestStatus.RUNNING
    if test.started_at is None:
        test.started_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(test, attribute_names=["variants"])
    return test


@router.get("/{test_id}", response_model=ABTestRead)
async def read_test(test_id: UUID, db: DbSession) -> ABTest:
    return await _get_test(db, test_id)


@router.post("/{test_id}/events", status_code=status.HTTP_202_ACCEPTED)
async def ingest_ab_events(test_id: UUID, batch: ABEventBatch, db: DbSession) -> dict[str, int]:
    test = await _get_test(db, test_id)
    valid_ids = {v.id for v in test.variants}
    rows: list[ABTestEvent] = []
    for ev in batch.events:
        if ev.variant_id not in valid_ids:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"variant {ev.variant_id} does not belong to test {test_id}",
            )
        rows.append(
            ABTestEvent(
                variant_id=ev.variant_id,
                event_type=ev.event_type,
                occurred_at=ev.occurred_at,
                session_hash=ev.session_hash,
            )
        )
    db.add_all(rows)
    await db.commit()
    return {"events_written": len(rows)}


@router.get("/{test_id}/results", response_model=ABTestResults)
async def get_results(test_id: UUID, db: DbSession) -> ABTestResults:
    test = await _get_test(db, test_id)

    counts_stmt = (
        select(
            ABTestEvent.variant_id,
            ABTestEvent.event_type,
            func.count(func.distinct(ABTestEvent.session_hash)).label("uniq"),
        )
        .where(ABTestEvent.variant_id.in_([v.id for v in test.variants]))
        .group_by(ABTestEvent.variant_id, ABTestEvent.event_type)
    )
    counts: dict[tuple[UUID, ABTestEventType], int] = {}
    for variant_id, event_type, uniq in (await db.execute(counts_stmt)).all():
        counts[(variant_id, event_type)] = uniq

    stats_input = [
        VariantStats(
            variant_id=str(v.id),
            label=v.label,
            impressions=counts.get((v.id, ABTestEventType.IMPRESSION), 0),
            clicks=counts.get((v.id, ABTestEventType.CLICK), 0),
        )
        for v in test.variants
    ]
    evaluation = evaluate(
        stats_input,
        min_impressions_per_variant=test.min_impressions_per_variant,
        confidence_target=test.confidence_target,
    )

    # Auto-decide if guardrails are met
    winner_uuid: UUID | None = None
    if evaluation.recommended_winner is not None:
        winner_uuid = UUID(evaluation.recommended_winner)
        if test.status == ABTestStatus.RUNNING:
            test.status = ABTestStatus.DECIDED
            test.decided_at = datetime.now(UTC)
            test.winner_variant_id = winner_uuid
            await db.commit()

    return ABTestResults(
        test_id=test.id,
        status=test.status,
        variants=[
            ABVariantResult(
                variant_id=UUID(r.variant_id),
                label=r.label,
                impressions=r.impressions,
                clicks=r.clicks,
                ctr=r.ctr,
                ctr_ci_low=r.ctr_ci_low,
                ctr_ci_high=r.ctr_ci_high,
                prob_best=r.prob_best,
            )
            for r in evaluation.variants
        ],
        has_enough_data=evaluation.has_enough_data,
        recommended_winner=winner_uuid,
        decision_confidence=evaluation.decision_confidence,
        explain=evaluation.explain,
    )


async def _get_test(db: AsyncSession, test_id: UUID) -> ABTest:
    stmt = select(ABTest).where(ABTest.id == test_id).options(selectinload(ABTest.variants))
    test = (await db.execute(stmt)).scalar_one_or_none()
    if test is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "test not found")
    return test
