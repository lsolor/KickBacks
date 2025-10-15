from __future__ import annotations

import datetime as dt

import pytest
from httpx import ASGITransport, AsyncClient

from kickback.core import flags
from kickback.core.types import PermissionRole
from kickback.domain.models import Document, Permission, User


@pytest.mark.anyio
async def test_signal_permission_denied(app, api_token, session_factory):
    async with session_factory() as session:
        user = User(email="viewer@example.com")
        session.add(user)
        await session.flush()
        document = Document(external_key="sig-doc", title="Sig Doc", owner_id=user.id)
        session.add(document)
        await session.flush()
        permission = Permission(doc_id=document.id, user_id=user.id, role=PermissionRole.VIEWER)
        session.add(permission)
        await session.commit()
        doc_id = document.id
        user_id = user.id

    headers = {"X-API-KEY": api_token}
    payload = {
        "doc_id": doc_id,
        "user_id": user_id,
        "kind": "update",
        "occurred_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    }

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post("/v1/signals", json=payload, headers=headers)

    assert response.status_code == 403


@pytest.mark.anyio
async def test_signal_idempotency(app, api_token, session_factory, monkeypatch):
    async with session_factory() as session:
        user = User(email="editor@example.com")
        session.add(user)
        await session.flush()
        document = Document(external_key="sig-doc2", title="Sig Doc 2", owner_id=user.id)
        session.add(document)
        await session.flush()
        permission = Permission(doc_id=document.id, user_id=user.id, role=PermissionRole.OWNER)
        session.add(permission)
        await session.commit()
        doc_id = document.id
        user_id = user.id

    headers = {"X-API-KEY": api_token}
    payload = {
        "doc_id": doc_id,
        "user_id": user_id,
        "kind": "create",
        "occurred_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "idem_key": "signal-123",
    }

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        first = await client.post("/v1/signals", json=payload, headers=headers)
        dup = await client.post("/v1/signals", json=payload, headers=headers)

    assert first.status_code == 201
    assert dup.status_code == 409


@pytest.mark.anyio
async def test_signal_idempotency_guard(app, api_token, session_factory, monkeypatch):
    async with session_factory() as session:
        user = User(email="guard@example.com")
        session.add(user)
        await session.flush()
        document = Document(external_key="sig-guard", title="Sig Guard", owner_id=user.id)
        session.add(document)
        await session.flush()
        permission = Permission(doc_id=document.id, user_id=user.id, role=PermissionRole.OWNER)
        session.add(permission)
        await session.commit()
        doc_id = document.id
        user_id = user.id

    class FakeRedis:
        def __init__(self):
            self.store: dict[str, str] = {}

        async def set(self, key, value, nx=False, ex=None):
            if nx and key in self.store:
                return False
            self.store[key] = value
            return True

    fake_redis = FakeRedis()

    async def fake_get_redis():
        return fake_redis

    monkeypatch.setattr(flags, "idempotency_guard_enabled", lambda: True)
    monkeypatch.setattr("kickback.core.cache.get_redis", fake_get_redis)

    headers = {"X-API-KEY": api_token}
    payload = {
        "doc_id": doc_id,
        "user_id": user_id,
        "kind": "create",
        "occurred_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "idem_key": "redis-guard",
    }

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        first = await client.post("/v1/signals", json=payload, headers=headers)
        dup = await client.post("/v1/signals", json=payload, headers=headers)

    assert first.status_code == 201
    assert dup.status_code == 409
