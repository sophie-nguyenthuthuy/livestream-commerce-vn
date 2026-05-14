from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from pydantic import Field

from app.schemas.common import APIModel


class ProductCreate(APIModel):
    sku: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=255)
    category: str = Field(min_length=1, max_length=64)
    price_vnd: Decimal = Field(gt=Decimal("0"))
    cost_vnd: Decimal | None = None
    description: str | None = None
    image_url: str | None = None


class ProductRead(APIModel):
    id: UUID
    sku: str
    name: str
    category: str
    price_vnd: Decimal
    cost_vnd: Decimal | None
    description: str | None
    image_url: str | None
