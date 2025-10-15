from __future__ import annotations

import pytest
from fastapi import HTTPException, status
from httpx import ASGITransport, AsyncClient

from kickback.api import deps


@pytest.mark.anyio
async def test_api_key_required(app, api_token):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post("/v1/documents", json={"external_key": "ext", "title": "Doc", "owner_id": 1})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.anyio
async def test_rate_limit_returns_429(app, api_token):
    async def _rate_limit():
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limited")

    app.dependency_overrides[deps.enforce_rate_limit] = _rate_limit

    headers = {"X-API-KEY": api_token}
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/v1/documents/1", headers=headers)

    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
