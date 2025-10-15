from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from kickback.domain import schemas
from kickback.infra.repositories.search_repo import SearchRepository


@dataclass
class SearchService:
    session: AsyncSession

    def __post_init__(self) -> None:
        self.repo = SearchRepository(self.session)

    async def leaderboard(self, window: str, limit: int) -> list[schemas.LeaderboardEntry]:
        since_date = self._parse_window(window)
        rows = await self.repo.leaderboard(since=since_date, limit=limit)
        return [
            schemas.LeaderboardEntry(
                doc_id=row.doc_id,
                score=float(row.recency_score),
                views=row.views,
                edits=row.edits,
            )
            for row in rows
        ]

    async def daily(self, doc_id: int) -> list[schemas.SignalsDailyEntry]:
        rows = await self.repo.daily_for_doc(doc_id=doc_id)
        return [
            schemas.SignalsDailyEntry(
                doc_id=row.doc_id,
                day=row.day,
                views=row.views,
                edits=row.edits,
                recency_score=float(row.recency_score),
            )
            for row in rows
        ]

    def _parse_window(self, window: str) -> dt.date:
        if window.endswith("d"):
            days = int(window[:-1])
            delta = dt.timedelta(days=days)
        elif window.endswith("h"):
            hours = int(window[:-1])
            delta = dt.timedelta(hours=hours)
        else:
            raise ValueError("Invalid window format")
        return (dt.datetime.now(dt.timezone.utc) - delta).date()
