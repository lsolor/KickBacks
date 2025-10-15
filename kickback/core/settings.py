from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class RateLimitSettings(BaseModel):
    per_min: int = Field(default=100, ge=1)
    burst: int = Field(default=100, ge=1)


class FlagSettings(BaseModel):
    ff_projector_enabled: bool = True
    ff_cache_enabled: bool = True
    ff_idempotency_redis_guard: bool = False


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="KICK_", env_file=None, extra="ignore")

    database_url: str = (
        "postgresql+asyncpg://kick:kick@localhost:5432/kick"  # sensible local default
    )
    redis_url: str = "redis://localhost:6379/0"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    api_key_header: str = "X-API-KEY"
    rate_limit: RateLimitSettings = RateLimitSettings()
    flags: FlagSettings = FlagSettings()


@lru_cache
def get_settings() -> Settings:
    return Settings()
