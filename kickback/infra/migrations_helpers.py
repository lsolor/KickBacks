from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from kickback.core.settings import get_settings


def get_migration_engine() -> AsyncEngine:
    settings = get_settings()
    return create_async_engine(settings.database_url, echo=False)
