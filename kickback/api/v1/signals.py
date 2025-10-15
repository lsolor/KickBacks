from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from kickback.api import deps
from kickback.domain import schemas
from kickback.services.signals import PermissionDeniedError, SignalConflictError, SignalsService


router = APIRouter(dependencies=[Depends(deps.enforce_rate_limit)])


@router.post("/signals", response_model=schemas.SignalRead, status_code=status.HTTP_201_CREATED)
async def ingest_signal(
    payload: schemas.SignalCreate,
    service: SignalsService = Depends(deps.get_signals_service),
) -> schemas.SignalRead:
    try:
        return await service.ingest_signal(payload)
    except PermissionDeniedError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
    except SignalConflictError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Duplicate signal")
