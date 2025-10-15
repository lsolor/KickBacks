from __future__ import annotations

from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

from kickback.core import flags
from kickback.infra.repositories import documents_repo
from kickback.domain.models import Document, User


@pytest.mark.anyio
async def test_document_create_conflict(app, api_token, session_factory):
    async with session_factory() as session:
        user = User(email="doc-owner@example.com")
        session.add(user)
        await session.commit()
        owner_id = user.id

    headers = {"X-API-KEY": api_token}
    payload = {"external_key": "doc-123", "title": "Doc", "owner_id": owner_id}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        first = await client.post("/v1/documents", json=payload, headers=headers)
        dup = await client.post("/v1/documents", json=payload, headers=headers)

    assert first.status_code == 201
    assert dup.status_code == 409


@pytest.mark.anyio
async def test_document_cache_hit_and_negative(app, api_token, session_factory, monkeypatch):
    async with session_factory() as session:
        user = User(email="cache-owner@example.com")
        session.add(user)
        await session.flush()
        doc = Document(external_key="cache-doc", title="Cache Doc", owner_id=user.id)
        session.add(doc)
        await session.commit()
        doc_id = doc.id

    cache_store: dict[str, Any] = {}

    async def fake_get(key: str):
        return cache_store.get(key)

    async def fake_set(key: str, value: Any, ttl: int):
        cache_store[key] = value

    async def fake_forget(key: str):
        cache_store.pop(key, None)

    monkeypatch.setattr(flags, "cache_enabled", lambda: True)
    monkeypatch.setattr("kickback.core.cache.cache_get", fake_get)
    monkeypatch.setattr("kickback.core.cache.cache_set", fake_set)
    monkeypatch.setattr("kickback.core.cache.cache_forget", fake_forget)

    call_counter = {"count": 0}
    original_get = documents_repo.DocumentRepository.get

    async def counting_get(self, document_id: int):
        call_counter["count"] += 1
        return await original_get(self, document_id)

    monkeypatch.setattr(documents_repo.DocumentRepository, "get", counting_get)

    headers = {"X-API-KEY": api_token}
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        await client.get(f"/v1/documents/{doc_id}", headers=headers)
        await client.get(f"/v1/documents/{doc_id}", headers=headers)

    assert call_counter["count"] == 1

    # Negative cache
    call_counter["count"] = 0
    cache_store.clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        first = await client.get("/v1/documents/9999", headers=headers)
        second = await client.get("/v1/documents/9999", headers=headers)

    assert first.status_code == 404
    assert second.status_code == 404
    assert call_counter["count"] == 1
