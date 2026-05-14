from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from app.api.deps import DbSession, ScriptDep
from app.models.script import Dialect, ScriptIntent, ScriptTemplate
from app.schemas.script import (
    ScriptGenerateRequest,
    ScriptGenerateResponse,
    ScriptRead,
    ScriptSave,
)
from app.services.script_service import ScriptGenerationError

router = APIRouter()


@router.post("/generate", response_model=ScriptGenerateResponse)
async def generate(req: ScriptGenerateRequest, svc: ScriptDep) -> ScriptGenerateResponse:
    try:
        return await svc.generate(req)
    except ScriptGenerationError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc)) from exc


@router.post("", response_model=ScriptRead, status_code=status.HTTP_201_CREATED)
async def save_script(payload: ScriptSave, db: DbSession) -> ScriptTemplate:
    script = ScriptTemplate(**payload.model_dump())
    db.add(script)
    await db.commit()
    await db.refresh(script)
    return script


@router.get("", response_model=list[ScriptRead])
async def list_scripts(
    db: DbSession,
    dialect: Dialect | None = Query(default=None),
    intent: ScriptIntent | None = Query(default=None),
    product_id: UUID | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[ScriptTemplate]:
    stmt = select(ScriptTemplate)
    if dialect:
        stmt = stmt.where(ScriptTemplate.dialect == dialect)
    if intent:
        stmt = stmt.where(ScriptTemplate.intent == intent)
    if product_id:
        stmt = stmt.where(ScriptTemplate.product_id == product_id)
    stmt = stmt.order_by(ScriptTemplate.upvotes.desc(), ScriptTemplate.created_at.desc()).limit(
        limit
    )
    return list((await db.execute(stmt)).scalars().all())


@router.post("/{script_id}/upvote", response_model=ScriptRead)
async def upvote(script_id: UUID, db: DbSession) -> ScriptTemplate:
    script = await db.get(ScriptTemplate, script_id)
    if script is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "script not found")
    script.upvotes += 1
    await db.commit()
    await db.refresh(script)
    return script
