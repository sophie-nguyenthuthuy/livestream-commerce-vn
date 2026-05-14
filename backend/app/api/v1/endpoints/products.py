from __future__ import annotations

import unicodedata
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.api.deps import DbSession
from app.models.product import Product
from app.schemas.common import Page
from app.schemas.product import ProductCreate, ProductRead

router = APIRouter()


def _normalize(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text)
    no_accents = "".join(c for c in nfkd if not unicodedata.combining(c))
    return no_accents.lower().strip()


@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
async def create_product(payload: ProductCreate, db: DbSession) -> Product:
    product = Product(**payload.model_dump(), name_normalized=_normalize(payload.name))
    db.add(product)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "sku already exists") from exc
    await db.refresh(product)
    return product


@router.get("", response_model=Page[ProductRead])
async def list_products(
    db: DbSession,
    q: str | None = Query(default=None, max_length=128),
    category: str | None = Query(default=None, max_length=64),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> Page[ProductRead]:
    stmt = select(Product)
    count_stmt = select(func.count(Product.id))
    if q:
        like = f"%{_normalize(q)}%"
        stmt = stmt.where(Product.name_normalized.like(like))
        count_stmt = count_stmt.where(Product.name_normalized.like(like))
    if category:
        stmt = stmt.where(Product.category == category)
        count_stmt = count_stmt.where(Product.category == category)

    total = (await db.execute(count_stmt)).scalar_one()
    stmt = stmt.order_by(Product.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    items = list((await db.execute(stmt)).scalars().all())
    return Page[ProductRead](
        items=[ProductRead.model_validate(p) for p in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{product_id}", response_model=ProductRead)
async def read_product(product_id: UUID, db: DbSession) -> Product:
    product = await db.get(Product, product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "product not found")
    return product
