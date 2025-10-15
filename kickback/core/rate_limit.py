from __future__ import annotations

import asyncio
import logging
import time
from pathlib import Path

from redis.asyncio import Redis

from .cache import get_redis
from .settings import get_settings


logger = logging.getLogger(__name__)

_script_sha: str | None = None
_sha_lock = asyncio.Lock()


async def _load_script(client: Redis) -> str:
    global _script_sha
    if _script_sha:
        return _script_sha

    async with _sha_lock:
        if _script_sha is None:
            script_path = Path(__file__).with_name("ratelimit_lua.lua")
            source = script_path.read_text(encoding="utf-8")
            _script_sha = await client.script_load(source)
            logger.info("Loaded rate limit Lua script", extra={"sha": _script_sha})
    assert _script_sha is not None
    return _script_sha


class RateLimitResult:
    __slots__ = ("allowed", "remaining")

    def __init__(self, allowed: bool, remaining: float):
        self.allowed = allowed
        self.remaining = remaining


async def check_rate_limit(client_key: str) -> RateLimitResult:
    settings = get_settings()
    rate = settings.rate_limit.per_min / 60
    burst = settings.rate_limit.burst

    redis = await get_redis()
    sha = await _load_script(redis)

    now = time.time()
    allowed, remaining = await redis.evalsha(
        sha, 2, f"rl:{client_key}:tokens", f"rl:{client_key}:ts", burst, rate, now, 1
    )

    return RateLimitResult(bool(allowed), float(remaining))
