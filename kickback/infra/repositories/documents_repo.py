from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from kickback.domain import models, schemas


class DocumentRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, payload: schemas.DocumentCreate) -> models.Document:
        document = models.Document(
            external_key=payload.external_key,
            title=payload.title,
            owner_id=payload.owner_id,
        )
        self._session.add(document)
        try:
            await self._session.flush()
        except IntegrityError as exc:
            raise DuplicateDocumentError(str(exc)) from exc
        return document

    async def get(self, document_id: int) -> models.Document | None:
        result = await self._session.execute(
            sa.select(models.Document).where(models.Document.id == document_id)
        )
        return result.scalar_one_or_none()

    async def get_by_external_key(self, external_key: str) -> models.Document | None:
        result = await self._session.execute(
            sa.select(models.Document).where(models.Document.external_key == external_key)
        )
        return result.scalar_one_or_none()


class DuplicateDocumentError(Exception):
    pass
