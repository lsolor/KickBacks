from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator
from typing import Awaitable

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

os.environ.setdefault("KICK_FLAGS__FF_CACHE_ENABLED", "false")
os.environ.setdefault("KICK_FLAGS__FF_IDEMPOTENCY_REDIS_GUARD", "false")
os.environ.setdefault("KICK_FLAGS__FF_PROJECTOR_ENABLED", "true")

from kickback.api.app import create_app  # noqa: E402
from kickback.api import deps  # noqa: E402
from kickback.core import settings  # noqa: E402
from kickback.core.security import generate_api_key  # noqa: E402
from kickback.core.types import ApiKeyStatus  # noqa: E402
from kickback.domain.models import ApiKey, Base  # noqa: E402


settings.get_settings.cache_clear()


@pytest.fixture(autouse=True)
def _stub_redis(monkeypatch):
    class DummyRedis:
        def __init__(self):
            self.store: dict[str, str] = {}

        async def get(self, key: str):
            return self.store.get(key)

        async def set(self, key: str, value: str, ex: int | None = None, nx: bool = False):
            if nx and key in self.store:
                return False
            self.store[key] = value
            return True

        async def delete(self, key: str):
            self.store.pop(key, None)

        async def script_load(self, source: str) -> str:
            return "stub-sha"

        async def evalsha(self, sha: str, numkeys: int, *args):
            # allow all requests by default
            return (1, 100)

    dummy = DummyRedis()

    async def fake_get_redis():
        return dummy

    async def fake_load_script(_):
        return "stub-sha"

    monkeypatch.setattr("kickback.core.cache.get_redis", fake_get_redis)
    monkeypatch.setattr("kickback.core.rate_limit.get_redis", fake_get_redis)
    monkeypatch.setattr("kickback.services.signals.get_redis", fake_get_redis)
    monkeypatch.setattr("kickback.core.rate_limit._load_script", fake_load_script)



@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture()
async def async_engine(tmp_path):
    db_path = tmp_path / "test.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture()
def session_factory(async_engine):
    return async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture()
async def session(session_factory) -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        try:
            yield session
        finally:
            if session.in_transaction():
                await session.rollback()
            await session.close()


@pytest.fixture()
async def api_token(session_factory) -> str:
    generated = generate_api_key()
    async with session_factory() as session:
        api_key = ApiKey(
            client_name="test",
            key_hash=generated.key_hash,
            salt=generated.salt,
            roles={"admin": True},
            status=ApiKeyStatus.ACTIVE,
        )
        session.add(api_key)
        await session.commit()
    return generated.raw_key


@pytest.fixture()
async def app(session_factory, monkeypatch) -> FastAPI:
    application = create_app()

    async def _get_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                if session.in_transaction():
                    await session.rollback()
                raise
            finally:
                await session.close()

    application.dependency_overrides[deps.get_session] = _get_session
    return application


@pytest.fixture()
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
