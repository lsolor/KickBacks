from __future__ import annotations

import asyncio
import datetime as dt
import logging
from typing import Optional

import typer
import uvicorn

from kickback.core.db import get_sessionmaker
from kickback.domain import models
from kickback.domain.schemas import ApiKeyCreate
from kickback.core.types import PermissionRole, SignalKind
from kickback.services.api_keys import ApiKeyService
from kickback.services.projector import SignalProjector


app = typer.Typer(help="Kickback operational CLI")
logger = logging.getLogger(__name__)


def _run_async(func, *args, **kwargs):
    return asyncio.run(func(*args, **kwargs))


@app.command()
def dev(host: str = "0.0.0.0", port: int = 8000, reload: bool = True):
    """Start the development server."""
    uvicorn.run("kickback.main:app", host=host, port=port, reload=reload, factory=False)


@app.command()
def seed():
    """Seed the database with sample data."""

    async def _seed():
        sessionmaker = get_sessionmaker()
        async with sessionmaker() as session:
            user = models.User(email="owner@example.com")
            session.add(user)
            await session.flush()

            document = models.Document(external_key="doc-001", title="First Doc", owner_id=user.id)
            session.add(document)

            permission = models.Permission(doc_id=document.id, user_id=user.id, role=PermissionRole.OWNER)
            session.add(permission)

            now = dt.datetime.now(dt.timezone.utc)
            session.add_all(
                [
                    models.Signal(
                        doc_id=document.id,
                        user_id=user.id,
                        kind=SignalKind.CREATE,
                        occurred_at=now,
                    ),
                    models.Signal(
                        doc_id=document.id,
                        user_id=user.id,
                        kind=SignalKind.VIEW,
                        occurred_at=now,
                    ),
                ]
            )
            await session.commit()
        logger.info("Database seeded")

    _run_async(_seed)


@app.command()
def projector():
    """Run the projector continuously."""

    async def _run():
        sessionmaker = get_sessionmaker()
        async with sessionmaker() as session:
            projector = SignalProjector(session=session)
            await projector.run_forever()

    _run_async(_run)


@app.command()
def create_key(client: str, expires_in_days: Optional[int] = typer.Option(None, min=1)):
    """Create a new API key."""

    async def _create():
        sessionmaker = get_sessionmaker()
        async with sessionmaker() as session:
            service = ApiKeyService(session=session)
            expires_at = None
            if expires_in_days:
                expires_at = dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=expires_in_days)
            key = await service.create(
                ApiKeyCreate(client_name=client, roles={"admin": False}, expires_at=expires_at)
            )
            await session.commit()
            print(f"API key created for {client}: {key.raw_key}")

    _run_async(_create)


def main():
    app()
