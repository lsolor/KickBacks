from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from kickback.core.db import session_scope
from kickback.core.rate_limit import check_rate_limit
from kickback.core.security import verify_api_key
from kickback.core.settings import get_settings
from kickback.infra.repositories.api_keys_repo import ApiKeyRepository
from kickback.services.api_keys import ApiKeyService
from kickback.services.documents import DocumentService
from kickback.services.projector import SignalProjector
from kickback.services.search import SearchService
from kickback.services.signals import SignalsService


async def get_session() -> AsyncIterator[AsyncSession]:
    async for session in session_scope():
        yield session


async def require_api_key(
    request: Request,
    session: AsyncSession = Depends(get_session),
    api_key_header: str | None = Header(default=None, alias=get_settings().api_key_header),
):
    if not api_key_header:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing API key")

    repo = ApiKeyRepository(session)
    active_keys = await repo.fetch_active()
    for key in active_keys:
        if verify_api_key(api_key_header, key.salt, key.key_hash):
            request.state.api_client = key
            return key

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")


async def enforce_rate_limit(api_key=Depends(require_api_key)):
    result = await check_rate_limit(str(api_key.id))
    if not result.allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={"Retry-After": "60"},
        )


async def get_document_service(session: AsyncSession = Depends(get_session)) -> DocumentService:
    return DocumentService(session=session)


async def get_signals_service(session: AsyncSession = Depends(get_session)) -> SignalsService:
    return SignalsService(session=session)


async def get_projector(session: AsyncSession = Depends(get_session)) -> SignalProjector:
    return SignalProjector(session=session)


async def get_search_service(session: AsyncSession = Depends(get_session)) -> SearchService:
    return SearchService(session=session)


async def get_api_key_service(session: AsyncSession = Depends(get_session)) -> ApiKeyService:
    return ApiKeyService(session=session)
