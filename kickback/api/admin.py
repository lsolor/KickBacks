from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status

from kickback.api import deps
from kickback.core import flags
from kickback.services.projector import SignalProjector


router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(deps.enforce_rate_limit)])


async def require_admin(request: Request):
    client = getattr(request.state, "api_client", None)
    roles = getattr(client, "roles", {})
    if not roles or not roles.get("admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return client


@router.post("/projector/run-once", dependencies=[Depends(require_admin)])
async def projector_run_once(projector: SignalProjector = Depends(deps.get_projector)) -> dict[str, int]:
    if not flags.projector_enabled():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Projector disabled")
    processed = await projector.run_once()
    return {"processed": processed}
