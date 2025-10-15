from __future__ import annotations

import datetime as dt

import pytest
from httpx import ASGITransport, AsyncClient

from kickback.core.types import PermissionRole, SignalKind
from kickback.domain import models
from kickback.services.projector import SignalProjector


@pytest.mark.anyio
async def test_leaderboard_and_daily(app, api_token, session_factory):
    now = dt.datetime.now(dt.timezone.utc)
    async with session_factory() as session:
        user = models.User(email="search@example.com")
        session.add(user)
        await session.flush()
        document = models.Document(external_key="search-doc", title="Search Doc", owner_id=user.id)
        session.add(document)
        await session.flush()
        permission = models.Permission(doc_id=document.id, user_id=user.id, role=PermissionRole.OWNER)
        session.add(permission)

        session.add_all(
            [
                models.Signal(
                    doc_id=document.id,
                    user_id=user.id,
                    kind=SignalKind.VIEW,
                    occurred_at=now - dt.timedelta(days=1),
                ),
                models.Signal(
                    doc_id=document.id,
                    user_id=user.id,
                    kind=SignalKind.UPDATE,
                    occurred_at=now,
                ),
            ]
        )
        await session.commit()
        doc_id = document.id

    async with session_factory() as session:
        projector = SignalProjector(session=session, batch_size=50)
        await projector.run_once()
        await session.commit()

    headers = {"X-API-KEY": api_token}
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        leaderboard = await client.get("/v1/search/leaderboard", headers=headers)
        daily = await client.get(f"/v1/search/signals/daily?doc_id={doc_id}", headers=headers)

    assert leaderboard.status_code == 200
    assert len(leaderboard.json()) >= 1
    assert leaderboard.json()[0]["doc_id"] == doc_id

    assert daily.status_code == 200
    body = daily.json()
    assert len(body) >= 1
    assert body[0]["doc_id"] == doc_id
