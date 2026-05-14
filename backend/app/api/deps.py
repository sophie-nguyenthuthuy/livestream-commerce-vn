from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.services.script_service import ScriptService


async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async for s in get_session():
        yield s


def script_service() -> ScriptService:
    return ScriptService()


DbSession = Annotated[AsyncSession, Depends(db_session)]
ScriptDep = Annotated[ScriptService, Depends(script_service)]
