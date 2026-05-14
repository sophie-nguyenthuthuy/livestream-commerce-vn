from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field, model_validator

from app.models.ab_test import ABTestEventType, ABTestStatus
from app.schemas.common import APIModel


class ABTestVariantCreate(APIModel):
    label: str = Field(min_length=1, max_length=64)
    thumbnail_url: str = Field(min_length=1, max_length=512)
    weight: int = Field(ge=0, le=100, default=50)


class ABTestCreate(APIModel):
    name: str = Field(min_length=1, max_length=255)
    hypothesis: str | None = None
    product_id: UUID | None = None
    variants: list[ABTestVariantCreate] = Field(min_length=2, max_length=6)
    min_impressions_per_variant: int = Field(default=1000, ge=100)
    confidence_target: float = Field(default=0.95, ge=0.5, le=0.999)

    @model_validator(mode="after")
    def _check_weights_sum_to_100(self) -> ABTestCreate:
        total = sum(v.weight for v in self.variants)
        if total != 100:
            raise ValueError(f"variant weights must sum to 100, got {total}")
        labels = [v.label for v in self.variants]
        if len(set(labels)) != len(labels):
            raise ValueError("variant labels must be unique")
        return self


class ABTestVariantRead(APIModel):
    id: UUID
    label: str
    thumbnail_url: str
    weight: int


class ABTestRead(APIModel):
    id: UUID
    name: str
    hypothesis: str | None
    product_id: UUID | None
    status: ABTestStatus
    started_at: datetime | None
    decided_at: datetime | None
    min_impressions_per_variant: int
    confidence_target: float
    winner_variant_id: UUID | None
    variants: list[ABTestVariantRead]


class ABEventIngest(APIModel):
    variant_id: UUID
    event_type: ABTestEventType
    occurred_at: datetime
    session_hash: str = Field(min_length=1, max_length=64)


class ABEventBatch(APIModel):
    events: list[ABEventIngest] = Field(min_length=1, max_length=1000)


class ABVariantResult(APIModel):
    variant_id: UUID
    label: str
    impressions: int
    clicks: int
    ctr: float
    ctr_ci_low: float
    ctr_ci_high: float
    prob_best: float  # Bayesian P(variant is best)


class ABTestResults(APIModel):
    test_id: UUID
    status: ABTestStatus
    variants: list[ABVariantResult]
    has_enough_data: bool
    recommended_winner: UUID | None
    decision_confidence: float
    explain: str
