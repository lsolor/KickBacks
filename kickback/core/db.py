from __future__ import annotations

import logging
import time
from typing import AsyncIterator

from sqlalchemy import event
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from .settings import get_settings


logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def _create_engine(url: str | URL) -> AsyncEngine:
    engine = create_async_engine(url, echo=False, pool_pre_ping=True)

    @event.listens_for(engine.sync_engine, "before_cursor_execute")
    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):  # type: ignore[override]
        context._query_start_time = time.perf_counter()

    @event.listens_for(engine.sync_engine, "after_cursor_execute")
    def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):  # type: ignore[override]
        start = getattr(context, "_query_start_time", None)
        if start is None:
            return
        elapsed = (time.perf_counter() - start) * 1000
        if elapsed > 100:
            logger.warning(
                "Slow query detected",
                extra={"elapsed_ms": round(elapsed, 2), "statement": statement[:200]},
            )

    return engine


def get_engine() -> AsyncEngine:
    global _engine, _sessionmaker
    if _engine is None:
        settings = get_settings()
        _engine = _create_engine(settings.database_url)
        _sessionmaker = async_sessionmaker(_engine, expire_on_commit=False)
    assert _engine is not None
    return _engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    global _sessionmaker
    if _sessionmaker is None:
        get_engine()
    assert _sessionmaker is not None
    return _sessionmaker


async def session_scope() -> AsyncIterator[AsyncSession]:
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
