from __future__ import annotations

from dataclasses import dataclass

from core_common.models import AuditEntity


@dataclass(slots=True)
class Notification(AuditEntity):
    user_id: str = ""
    event_type: str = ""
    message: str = ""
    read: bool = False
