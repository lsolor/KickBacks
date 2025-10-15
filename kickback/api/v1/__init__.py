from fastapi import APIRouter

from . import api_keys, documents, search, signals

router = APIRouter(prefix="/v1")
router.include_router(documents.router, tags=["documents"])
router.include_router(signals.router, tags=["signals"])
router.include_router(search.router, prefix="/search", tags=["search"])
router.include_router(api_keys.router, tags=["api-keys"])

__all__ = ["router"]
