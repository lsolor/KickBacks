from __future__ import annotations

import datetime as dt
from typing import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from kickback.domain import models


class SearchRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def upsert_daily(
        self,
        doc_id: int,
        day: dt.date,
        views: int,
        edits: int,
        recency_score: float,
    ) -> None:
        bind = self._session.get_bind()
        dialect = bind.dialect.name if bind is not None else "postgresql"

        if dialect == "sqlite":
            insert_stmt = sqlite_insert(models.SearchSignalsDaily)
        else:
            insert_stmt = pg_insert(models.SearchSignalsDaily)

        stmt = insert_stmt.values(
            doc_id=doc_id,
            day=day,
            views=views,
            edits=edits,
            recency_score=recency_score,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["doc_id", "day"],
            set_={
                "views": views,
                "edits": edits,
                "recency_score": recency_score,
            },
        )
        await self._session.execute(stmt)

    async def leaderboard(self, since: dt.date, limit: int) -> Sequence[models.SearchSignalsDaily]:
        stmt = (
            sa.select(models.SearchSignalsDaily)
            .where(models.SearchSignalsDaily.day >= since)
            .order_by(models.SearchSignalsDaily.recency_score.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def daily_for_doc(self, doc_id: int) -> Sequence[models.SearchSignalsDaily]:
        stmt = (
            sa.select(models.SearchSignalsDaily)
            .where(models.SearchSignalsDaily.doc_id == doc_id)
            .order_by(models.SearchSignalsDaily.day.desc())
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_projector_state(self, name: str) -> models.ProjectorState | None:
        stmt = sa.select(models.ProjectorState).where(models.ProjectorState.name == name)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_projector_state(self, name: str, last_signal_id: int) -> None:
        existing = await self.get_projector_state(name)
        if existing:
            existing.last_signal_id = last_signal_id
        else:
            state = models.ProjectorState(name=name, last_signal_id=last_signal_id)
            self._session.add(state)
