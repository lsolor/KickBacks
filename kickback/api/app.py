from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from kickback.core.db import get_engine
from kickback.core.middleware import RequestContextMiddleware
from kickback.core.settings import get_settings

from . import admin, health
from .v1 import router as v1_router


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info("Starting Kickback", extra={"log_level": settings.log_level})
    engine = get_engine()
    try:
        yield
    finally:
        await engine.dispose()
        logger.info("Shutdown complete")


def create_app() -> FastAPI:
    app = FastAPI(title="Kickback", lifespan=lifespan)
    app.add_middleware(RequestContextMiddleware)
    app.include_router(health.router)
    app.include_router(v1_router)
    app.include_router(admin.router)
    return app
