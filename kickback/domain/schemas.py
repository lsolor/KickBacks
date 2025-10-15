from __future__ import annotations

import datetime as dt
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

from kickback.core.types import ApiKeyStatus, PermissionRole, SignalKind


class DocumentCreate(BaseModel):
    external_key: str
    title: str
    owner_id: int


class DocumentRead(BaseModel):
    id: int
    external_key: str
    title: str
    owner_id: int
    created_at: dt.datetime
    updated_at: dt.datetime


class SignalCreate(BaseModel):
    doc_id: int
    user_id: int
    kind: SignalKind
    occurred_at: dt.datetime
    idem_key: str | None = None


class SignalRead(BaseModel):
    id: int
    doc_id: int
    user_id: int
    kind: SignalKind
    occurred_at: dt.datetime
    idem_key: str | None


class LeaderboardQuery(BaseModel):
    window: str = Field(default="7d")
    limit: int = Field(default=10, ge=1, le=100)


class LeaderboardEntry(BaseModel):
    doc_id: int
    score: float
    views: int
    edits: int


class SignalsDailyQuery(BaseModel):
    doc_id: int


class SignalsDailyEntry(BaseModel):
    doc_id: int
    day: dt.date
    views: int
    edits: int
    recency_score: float


class ApiKeyCreate(BaseModel):
    client_name: str
    roles: dict[str, Any] = Field(default_factory=dict)
    expires_at: dt.datetime | None = None


class ApiKeyRead(BaseModel):
    id: int
    client_name: str
    status: ApiKeyStatus
    created_at: dt.datetime
    expires_at: dt.datetime | None


class ApiKeyWithSecret(ApiKeyRead):
    raw_key: str


class PermissionAssignment(BaseModel):
    user_id: int
    role: PermissionRole
