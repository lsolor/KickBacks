from __future__ import annotations

import logging

from fastapi import FastAPI

from .api.app import create_app
from .core.logging_config import configure_logging
from .core.settings import get_settings


configure_logging(get_settings().log_level)
app: FastAPI = create_app()

logger = logging.getLogger(__name__)
logger.debug("Kickback application instantiated")
