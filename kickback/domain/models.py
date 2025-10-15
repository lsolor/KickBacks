from __future__ import annotations

import datetime as dt
from typing import List, Optional

import sqlalchemy as sa
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from kickback.core.db import Base
from kickback.core.types import ApiKeyStatus, PermissionRole, SignalKind


TZDateTime = sa.types.DateTime(timezone=True)
JSONType = JSONB(astext_type=sa.Text()).with_variant(JSON(), "sqlite")
PKType = sa.BigInteger().with_variant(sa.Integer(), "sqlite")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(PKType, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(sa.String(255), unique=True, nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(TZDateTime, server_default=sa.func.now(), nullable=False)

    documents: Mapped[List["Document"]] = relationship("Document", back_populates="owner")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(PKType, primary_key=True, autoincrement=True)
    external_key: Mapped[str] = mapped_column(sa.String(255), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    owner_id: Mapped[int] = mapped_column(PKType, sa.ForeignKey("users.id"), nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(TZDateTime, server_default=sa.func.now(), nullable=False)
    updated_at: Mapped[dt.datetime] = mapped_column(
        TZDateTime, server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False
    )

    owner: Mapped[User] = relationship("User", back_populates="documents")
    permissions: Mapped[List["Permission"]] = relationship("Permission", back_populates="document")


class Permission(Base):
    __tablename__ = "permissions"
    __table_args__ = (sa.UniqueConstraint("doc_id", "user_id"),)

    id: Mapped[int] = mapped_column(PKType, primary_key=True, autoincrement=True)
    doc_id: Mapped[int] = mapped_column(PKType, sa.ForeignKey("documents.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(PKType, sa.ForeignKey("users.id"), nullable=False)
    role: Mapped[PermissionRole] = mapped_column(
        sa.Enum(PermissionRole, name="permission_role"), nullable=False, default=PermissionRole.VIEWER
    )

    document: Mapped[Document] = relationship("Document", back_populates="permissions")
    user: Mapped[User] = relationship("User")


class Signal(Base):
    __tablename__ = "signals"

    id: Mapped[int] = mapped_column(PKType, primary_key=True, autoincrement=True)
    doc_id: Mapped[int] = mapped_column(PKType, sa.ForeignKey("documents.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(PKType, sa.ForeignKey("users.id"), nullable=False)
    kind: Mapped[SignalKind] = mapped_column(sa.Enum(SignalKind, name="signal_kind"), nullable=False)
    occurred_at: Mapped[dt.datetime] = mapped_column(TZDateTime, nullable=False)
    idem_key: Mapped[Optional[str]] = mapped_column(sa.String(255), unique=True, nullable=True)

    document: Mapped[Document] = relationship("Document")
    user: Mapped[User] = relationship("User")


class ApiKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(PKType, primary_key=True, autoincrement=True)
    client_name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    key_hash: Mapped[str] = mapped_column(sa.String(64), nullable=False, unique=True)
    salt: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    roles: Mapped[dict] = mapped_column(JSONType, nullable=False, default=dict)
    status: Mapped[ApiKeyStatus] = mapped_column(
        sa.Enum(ApiKeyStatus, name="api_key_status"),
        nullable=False,
        default=ApiKeyStatus.ACTIVE,
    )
    created_at: Mapped[dt.datetime] = mapped_column(TZDateTime, server_default=sa.func.now(), nullable=False)
    expires_at: Mapped[Optional[dt.datetime]] = mapped_column(TZDateTime, nullable=True)


class SearchSignalsDaily(Base):
    __tablename__ = "search_signals_daily"
    __table_args__ = (sa.PrimaryKeyConstraint("doc_id", "day"),)

    doc_id: Mapped[int] = mapped_column(PKType, nullable=False)
    day: Mapped[dt.date] = mapped_column(sa.Date, nullable=False)
    views: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    edits: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    recency_score: Mapped[float] = mapped_column(sa.Numeric(scale=4, precision=12), nullable=False, default=0.0)


class ProjectorState(Base):
    __tablename__ = "projector_state"

    name: Mapped[str] = mapped_column(sa.String(100), primary_key=True)
    last_signal_id: Mapped[int] = mapped_column(PKType, nullable=False, default=0)
    updated_at: Mapped[dt.datetime] = mapped_column(TZDateTime, server_default=sa.func.now(), nullable=False)
