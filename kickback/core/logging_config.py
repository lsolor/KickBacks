from __future__ import annotations

import json
import logging
import sys
import time
from typing import Any, Dict


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(record.created)),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        standard = {
            "name",
            "msg",
            "args",
            "levelname",
            "levelno",
            "pathname",
            "filename",
            "module",
            "exc_info",
            "exc_text",
            "stack_info",
            "lineno",
            "funcName",
            "created",
            "msecs",
            "relativeCreated",
            "thread",
            "threadName",
            "processName",
            "process",
            "message",
        }
        extras = {key: value for key, value in record.__dict__.items() if key not in standard}
        payload.update(extras)
        return json.dumps(payload, default=str)


def configure_logging(level: str | None = None) -> None:
    logging.basicConfig(
        level=level or logging.INFO,
        format="%(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    root = logging.getLogger()
    for handler in root.handlers:
        handler.setFormatter(JsonFormatter())
