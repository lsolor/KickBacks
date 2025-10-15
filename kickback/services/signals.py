from __future__ import annotations

import datetime as dt
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from kickback.core import flags
from kickback.core.cache import get_redis
from kickback.core.types import PermissionRole, SignalKind
from kickback.domain import schemas
from kickback.infra.repositories.permissions_repo import PermissionRepository
from kickback.infra.repositories.signals_repo import DuplicateSignalError, SignalRepository


logger = logging.getLogger(__name__)


class PermissionDeniedError(Exception):
    ...


class SignalConflictError(Exception):
    ...


class SignalsService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = SignalRepository(session)
        self.permissions = PermissionRepository(session)

    async def ingest_signal(self, payload: schemas.SignalCreate) -> schemas.SignalRead:
        role = await self.permissions.get_role(payload.doc_id, payload.user_id)
        self._ensure_permission(role, payload.kind)

        if payload.idem_key and flags.idempotency_guard_enabled():
            await self._assert_idempotency(payload.idem_key)

        try:
            record = await self.repo.create(payload)
        except DuplicateSignalError as exc:
            raise SignalConflictError from exc

        return schemas.SignalRead(
            id=record.id,
            doc_id=record.doc_id,
            user_id=record.user_id,
            kind=record.kind,
            occurred_at=record.occurred_at,
            idem_key=record.idem_key,
        )

    def _ensure_permission(self, role: PermissionRole | None, kind: SignalKind) -> None:
        if role is None:
            raise PermissionDeniedError

        if kind in (SignalKind.UPDATE, SignalKind.CREATE) and role not in (
            PermissionRole.EDITOR,
            PermissionRole.OWNER,
        ):
            raise PermissionDeniedError

    async def _assert_idempotency(self, key: str) -> None:
        redis = await get_redis()
        inserted = await redis.set(f"idempotency:{key}", "1", nx=True, ex=60)
        if not inserted:
            raise SignalConflictError
