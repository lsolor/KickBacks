from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from kickback.core.types import PermissionRole
from kickback.domain import models


class PermissionRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_role(self, doc_id: int, user_id: int) -> PermissionRole | None:
        stmt = sa.select(models.Permission.role).where(
            models.Permission.doc_id == doc_id, models.Permission.user_id == user_id
        )
        result = await self._session.execute(stmt)
        role = result.scalar_one_or_none()
        return PermissionRole(role) if role else None

    async def assign(self, doc_id: int, user_id: int, role: PermissionRole) -> models.Permission:
        permission = models.Permission(doc_id=doc_id, user_id=user_id, role=role)
        self._session.add(permission)
        await self._session.flush()
        return permission
