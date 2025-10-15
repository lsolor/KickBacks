from __future__ import annotations

import enum
from typing import NewType


RequestId = NewType("RequestId", str)
ClientId = NewType("ClientId", str)


class PermissionRole(str, enum.Enum):
    VIEWER = "viewer"
    EDITOR = "editor"
    OWNER = "owner"


class SignalKind(str, enum.Enum):
    CREATE = "create"
    UPDATE = "update"
    VIEW = "view"


class ApiKeyStatus(str, enum.Enum):
    ACTIVE = "active"
    DISABLED = "disabled"
