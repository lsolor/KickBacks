from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from kickback.core.security import generate_api_key
from kickback.domain import schemas
from kickback.infra.repositories.api_keys_repo import ApiKeyRepository


@dataclass
class ApiKeyService:
    session: AsyncSession

    def __post_init__(self) -> None:
        self.repo = ApiKeyRepository(self.session)

    async def create(self, payload: schemas.ApiKeyCreate) -> schemas.ApiKeyWithSecret:
        generated = generate_api_key()
        record = await self.repo.create(
            client_name=payload.client_name,
            key_hash=generated.key_hash,
            salt=generated.salt,
            roles=payload.roles,
            expires_at=payload.expires_at,
        )
        return schemas.ApiKeyWithSecret(
            id=record.id,
            client_name=record.client_name,
            status=record.status,
            created_at=record.created_at,
            expires_at=record.expires_at,
            raw_key=generated.raw_key,
        )

    async def list_keys(self) -> list[schemas.ApiKeyRead]:
        keys = await self.repo.list_api_keys()
        return [
            schemas.ApiKeyRead(
                id=key.id,
                client_name=key.client_name,
                status=key.status,
                created_at=key.created_at,
                expires_at=key.expires_at,
            )
            for key in keys
        ]

    async def disable(self, api_key_id: int) -> None:
        await self.repo.disable(api_key_id)
