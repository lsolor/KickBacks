from __future__ import annotations

from .settings import get_settings


def projector_enabled() -> bool:
    return get_settings().flags.ff_projector_enabled


def cache_enabled() -> bool:
    return get_settings().flags.ff_cache_enabled


def idempotency_guard_enabled() -> bool:
    return get_settings().flags.ff_idempotency_redis_guard
