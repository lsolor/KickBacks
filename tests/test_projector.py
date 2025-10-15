from __future__ import annotations

import datetime as dt

import pytest

from kickback.core.types import PermissionRole, SignalKind
from kickback.domain import models
from kickback.services.projector import SignalProjector
from kickback.infra.repositories.search_repo import SearchRepository


@pytest.mark.anyio
async def test_projector_idempotent(session_factory):
    async with session_factory() as session:
        user = models.User(email="projector@example.com")
        session.add(user)
        await session.flush()
        document = models.Document(external_key="proj-doc", title="Proj Doc", owner_id=user.id)
        session.add(document)
        await session.flush()
        permission = models.Permission(doc_id=document.id, user_id=user.id, role=PermissionRole.OWNER)
        session.add(permission)

        now = dt.datetime.now(dt.timezone.utc)
        session.add_all(
            [
                models.Signal(
                    doc_id=document.id,
                    user_id=user.id,
                    kind=SignalKind.CREATE,
                    occurred_at=now,
                ),
                models.Signal(
                    doc_id=document.id,
                    user_id=user.id,
                    kind=SignalKind.VIEW,
                    occurred_at=now,
                ),
            ]
        )
        await session.commit()
        doc_id = document.id

    async with session_factory() as session:
        projector = SignalProjector(session=session, batch_size=10)
        processed_first = await projector.run_once()
        await session.commit()
        processed_second = await projector.run_once()
        await session.commit()

        assert processed_first == 2
        assert processed_second == 0

        repo = SearchRepository(session)
        rows = await repo.daily_for_doc(doc_id=doc_id)
        assert len(rows) == 1
        entry = rows[0]
        assert entry.views == 1
        assert entry.edits == 1
