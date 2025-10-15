from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from kickback.api import deps
from kickback.domain import schemas
from kickback.services.search import SearchService


router = APIRouter(dependencies=[Depends(deps.enforce_rate_limit)])


@router.get("/leaderboard", response_model=list[schemas.LeaderboardEntry])
async def leaderboard(
    window: str = Query(default="7d"),
    limit: int = Query(default=10, ge=1, le=100),
    service: SearchService = Depends(deps.get_search_service),
) -> list[schemas.LeaderboardEntry]:
    try:
        return await service.leaderboard(window=window, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/signals/daily", response_model=list[schemas.SignalsDailyEntry])
async def signals_daily(
    doc_id: int = Query(..., ge=1),
    service: SearchService = Depends(deps.get_search_service),
) -> list[schemas.SignalsDailyEntry]:
    return await service.daily(doc_id=doc_id)
