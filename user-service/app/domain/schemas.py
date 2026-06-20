from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class UserProfileCreate:
    display_name: str
    phone: str | None = None


@dataclass(slots=True)
class UserProfile:
    id: str
    auth_subject: str
    email: str | None
    display_name: str
    phone: str | None = None
    is_active: bool = True
    deleted_at: datetime | None = None
