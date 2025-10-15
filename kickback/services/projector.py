from __future__ import annotations

import asyncio
import datetime as dt
import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from kickback.core.types import SignalKind
from kickback.infra.repositories.search_repo import SearchRepository
from kickback.infra.repositories.signals_repo import SignalRepository


logger = logging.getLogger(__name__)


@dataclass
class SignalProjector:
    session: AsyncSession
    batch_size: int = 500
    name: str = "search_signals_projector"

    def __post_init__(self) -> None:
        self.signals_repo = SignalRepository(self.session)
        self.search_repo = SearchRepository(self.session)

    async def run_once(self) -> int:
        state = await self.search_repo.get_projector_state(self.name)
        last_id = state.last_signal_id if state else 0
        signals = await self.signals_repo.fetch_batch(last_id=last_id, limit=self.batch_size)
        if not signals:
            logger.info("Projector caught up", extra={"last_id": last_id})
            return 0

        aggregates: Dict[Tuple[int, dt.date], Dict[str, float]] = defaultdict(lambda: {"views": 0, "edits": 0})
        max_id = last_id
        now = dt.datetime.now(dt.timezone.utc)

        for signal in signals:
            max_id = max(max_id, signal.id)
            key = (signal.doc_id, signal.occurred_at.date())
            if signal.kind == SignalKind.VIEW:
                aggregates[key]["views"] += 1
            else:
                aggregates[key]["edits"] += 1

        for (doc_id, day), data in aggregates.items():
            age_days = (now.date() - day).days
            recency_score = data["views"] + data["edits"] * 2 + max(0, 10 - age_days)
            await self.search_repo.upsert_daily(
                doc_id=doc_id,
                day=day,
                views=int(data["views"]),
                edits=int(data["edits"]),
                recency_score=float(recency_score),
            )

        await self.search_repo.update_projector_state(self.name, max_id)
        logger.info("Projector advanced", extra={"processed": len(signals), "last_id": max_id})
        return len(signals)

    async def run_forever(self, sleep_seconds: float = 2.0) -> None:
        while True:
            processed = await self.run_once()
            if processed == 0:
                await asyncio.sleep(sleep_seconds)
