from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Awaitable, Callable

from redis.asyncio import Redis

from .settings import get_settings


logger = logging.getLogger(__name__)
_redis: Redis | None = None
_redis_lock = asyncio.Lock()


async def get_redis() -> Redis:
    global _redis
    if _redis is None:
        async with _redis_lock:
            if _redis is None:
                settings = get_settings()
                _redis = Redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
    assert _redis is not None
    return _redis


async def cache_get(key: str) -> Any | None:
    client = await get_redis()
    payload = await client.get(key)
    if payload is None:
        return None
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        logger.warning("Cache payload decode error", extra={"key": key})
        return None


async def cache_set(key: str, value: Any, ttl_seconds: int) -> None:
    client = await get_redis()
    payload = json.dumps(value, default=str)
    await client.set(key, payload, ex=ttl_seconds)


async def cache_forget(key: str) -> None:
    client = await get_redis()
    await client.delete(key)


async def cache_get_or_set(key: str, ttl_seconds: int, factory: Callable[[], Any | Awaitable[Any]]) -> Any:
    cached = await cache_get(key)
    if cached is not None:
        return cached

    result = factory()
    if asyncio.iscoroutine(result):
        result = await result
    await cache_set(key, result, ttl_seconds)
    return result
