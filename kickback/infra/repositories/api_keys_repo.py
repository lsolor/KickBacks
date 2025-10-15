from __future__ import annotations

import datetime as dt

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from kickback.core.types import ApiKeyStatus
from kickback.domain import models


class ApiKeyRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(
        self,
        client_name: str,
        key_hash: str,
        salt: str,
        roles: dict,
        expires_at: dt.datetime | None,
    ) -> models.ApiKey:
        record = models.ApiKey(
            client_name=client_name,
            key_hash=key_hash,
            salt=salt,
            roles=roles,
            expires_at=expires_at,
            status=ApiKeyStatus.ACTIVE,
        )
        self._session.add(record)
        await self._session.flush()
        return record

    async def get_active_by_hash(self, key_hash: str) -> models.ApiKey | None:
        stmt = sa.select(models.ApiKey).where(
            models.ApiKey.key_hash == key_hash, models.ApiKey.status == ApiKeyStatus.ACTIVE
        )
        result = await self._session.execute(stmt)
        api_key = result.scalar_one_or_none()
        if api_key and api_key.expires_at and api_key.expires_at < dt.datetime.now(dt.timezone.utc):
            return None
        return api_key

    async def list_api_keys(self, limit: int = 100) -> list[models.ApiKey]:
        stmt = sa.select(models.ApiKey).limit(limit).order_by(models.ApiKey.created_at.desc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def fetch_active(self) -> list[models.ApiKey]:
        stmt = sa.select(models.ApiKey).where(models.ApiKey.status == ApiKeyStatus.ACTIVE)
        result = await self._session.execute(stmt)
        keys = list(result.scalars().all())
        now = dt.datetime.now(dt.timezone.utc)
        return [key for key in keys if not key.expires_at or key.expires_at >= now]

    async def disable(self, api_key_id: int) -> None:
        api_key = await self._session.get(models.ApiKey, api_key_id)
        if api_key:
            api_key.status = ApiKeyStatus.DISABLED
