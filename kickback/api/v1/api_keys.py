from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status

from kickback.api import deps
from kickback.domain import schemas
from kickback.services.api_keys import ApiKeyService


router = APIRouter(
    dependencies=[Depends(deps.enforce_rate_limit)],
)


async def require_admin(request: Request):
    client = getattr(request.state, "api_client", None)
    roles = getattr(client, "roles", {})
    if not roles or not roles.get("admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return client


@router.post("/api-keys", response_model=schemas.ApiKeyWithSecret, dependencies=[Depends(require_admin)])
async def create_api_key(
    payload: schemas.ApiKeyCreate,
    service: ApiKeyService = Depends(deps.get_api_key_service),
) -> schemas.ApiKeyWithSecret:
    return await service.create(payload)


@router.get("/api-keys", response_model=list[schemas.ApiKeyRead], dependencies=[Depends(require_admin)])
async def list_api_keys(service: ApiKeyService = Depends(deps.get_api_key_service)) -> list[schemas.ApiKeyRead]:
    return await service.list_keys()


@router.post(
    "/api-keys/{api_key_id}/disable",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
async def disable_api_key(
    api_key_id: int,
    service: ApiKeyService = Depends(deps.get_api_key_service),
) -> None:
    await service.disable(api_key_id)
