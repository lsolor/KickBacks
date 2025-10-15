# Kickback

Kickback is a FastAPI-based async service that tracks document activity signals, projects them into daily search aggregates, and exposes a typed API with API-key authentication, rate limiting, and Redis-backed caching.

## Stack

- FastAPI + Uvicorn
- SQLAlchemy 2.0 (async) with PostgreSQL/asyncpg and Alembic
- Redis 7 for cache + Lua token bucket rate limiting
- Pydantic v2 + pydantic-settings for typed configuration
- Tenacity, Typer CLI, pytest/httpx/pytest-asyncio
- Tooling: Ruff, MyPy (strict), uv package manager

## Quick Start

```bash
# Install deps
uv sync

# Bring up infrastructure and API
docker compose up --build

# Run migrations
uv run alembic upgrade head

# Create an API key
uv run kickback-create-key --client demo

# Seed sample data
uv run kickback-seed
```

Example requests (replace `<token>` with the generated key):

```bash
curl -H "X-API-KEY: <token>" http://localhost:8000/health

curl -X POST http://localhost:8000/v1/documents \
     -H "Content-Type: application/json" \
     -H "X-API-KEY: <token>" \
     -d '{"external_key":"doc-123","title":"Doc","owner_id":1}'
```

Run the projector once via API:

```bash
curl -X POST http://localhost:8000/admin/projector/run-once -H "X-API-KEY: <token>"
```

Or continuously from the CLI:

```bash
uv run kickback-projector
```

## Feature Flags & Env Vars

Environment variables are prefixed with `KICK_`. Key settings:

- `KICK_DATABASE_URL`
- `KICK_REDIS_URL`
- `KICK_LOG_LEVEL`
- `KICK_API_KEY_HEADER` (default `X-API-KEY`)
- `KICK_RATE_LIMIT__PER_MIN` / `KICK_RATE_LIMIT__BURST`
- `KICK_FLAGS__FF_PROJECTOR_ENABLED`
- `KICK_FLAGS__FF_CACHE_ENABLED`
- `KICK_FLAGS__FF_IDEMPOTENCY_REDIS_GUARD`

All configuration is surfaced through `kickback.core.settings.Settings`.
