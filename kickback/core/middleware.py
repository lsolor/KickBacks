from __future__ import annotations

import contextvars
import logging
import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from .types import ClientId, RequestId


logger = logging.getLogger("kickback.request")

request_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar("request_id", default=None)
client_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar("client_id", default=None)


def get_request_id() -> RequestId | None:
    value = request_id_ctx.get()
    return RequestId(value) if value else None


def get_client_id() -> ClientId | None:
    value = client_id_ctx.get()
    return ClientId(value) if value else None


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start = time.perf_counter()
        rid = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        cid = request.headers.get("X-Client-ID") or "anonymous"
        token_req = request_id_ctx.set(rid)
        token_client = client_id_ctx.set(cid)

        try:
            response = await call_next(request)
        except Exception as exc:  # pragma: no cover - fallback logging
            logger.exception("request-error", extra={"request_id": rid, "client_id": cid})
            raise exc
        finally:
            request_id_ctx.reset(token_req)
            client_id_ctx.reset(token_client)

        latency = (time.perf_counter() - start) * 1000
        response.headers["X-Request-ID"] = rid
        logger.info(
            "request-complete",
            extra={
                "request_id": rid,
                "client_id": cid,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "lat_ms": round(latency, 2),
            },
        )
        return response
