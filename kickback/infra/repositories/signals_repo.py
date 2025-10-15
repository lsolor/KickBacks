from __future__ import annotations

import datetime as dt
from typing import Iterable, List

import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from kickback.domain import models, schemas


class SignalRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, payload: schemas.SignalCreate) -> models.Signal:
        signal = models.Signal(
            doc_id=payload.doc_id,
            user_id=payload.user_id,
            kind=payload.kind,
            occurred_at=payload.occurred_at,
            idem_key=payload.idem_key,
        )
        self._session.add(signal)
        try:
            await self._session.flush()
        except IntegrityError as exc:
            raise DuplicateSignalError from exc
        return signal

    async def fetch_batch(self, last_id: int, limit: int) -> list[models.Signal]:
        stmt = (
            sa.select(models.Signal)
            .where(models.Signal.id > last_id)
            .order_by(models.Signal.id)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def events_in_window(self, doc_ids: Iterable[int], since: dt.datetime) -> list[models.Signal]:
        stmt = (
            sa.select(models.Signal)
            .where(models.Signal.doc_id.in_(list(doc_ids)))
            .where(models.Signal.occurred_at >= since)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())


class DuplicateSignalError(Exception):
    ...
