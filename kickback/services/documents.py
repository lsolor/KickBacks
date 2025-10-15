from __future__ import annotations

import logging
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from kickback.core import flags
from kickback.core.cache import cache_forget, cache_get, cache_set
from kickback.domain import schemas
from kickback.infra.repositories.documents_repo import DocumentRepository, DuplicateDocumentError


logger = logging.getLogger(__name__)

_CACHE_KEY = "doc:{doc_id}"
_NEGATIVE_MARKER = "__not_found__"
POSITIVE_TTL = 60
NEGATIVE_TTL = 5


class DocumentServiceError(Exception):
    ...


class DocumentConflictError(DocumentServiceError):
    ...


class DocumentNotFoundError(DocumentServiceError):
    ...


@dataclass
class DocumentService:
    session: AsyncSession

    def __post_init__(self) -> None:
        self.repo = DocumentRepository(self.session)

    async def create_document(self, payload: schemas.DocumentCreate) -> schemas.DocumentRead:
        try:
            document = await self.repo.create(payload)
            if flags.cache_enabled():
                await cache_forget(_CACHE_KEY.format(doc_id=document.id))
            return schemas.DocumentRead(
                id=document.id,
                external_key=document.external_key,
                title=document.title,
                owner_id=document.owner_id,
                created_at=document.created_at,
                updated_at=document.updated_at,
            )
        except DuplicateDocumentError as exc:
            logger.info("Duplicate document detected", extra={"external_key": payload.external_key})
            raise DocumentConflictError from exc

    async def get_document(self, document_id: int) -> schemas.DocumentRead:
        cache_key = _CACHE_KEY.format(doc_id=document_id)
        if flags.cache_enabled():
            cached = await cache_get(cache_key)
            if cached is not None:
                if cached == _NEGATIVE_MARKER:
                    raise DocumentNotFoundError
                return schemas.DocumentRead(**cached)

        document = await self.repo.get(document_id)
        if not document:
            if flags.cache_enabled():
                await cache_set(cache_key, _NEGATIVE_MARKER, NEGATIVE_TTL)
            raise DocumentNotFoundError

        schema = schemas.DocumentRead(
            id=document.id,
            external_key=document.external_key,
            title=document.title,
            owner_id=document.owner_id,
            created_at=document.created_at,
            updated_at=document.updated_at,
        )

        if flags.cache_enabled():
            await cache_set(cache_key, schema.model_dump(), POSITIVE_TTL)
        return schema
