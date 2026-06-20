from __future__ import annotations

from dataclasses import dataclass, field

from core_common.models import AuditEntity


@dataclass(slots=True)
class Order(AuditEntity):
    user_id: str = ""
    status: str = "pending"
    total: int = 0
    lines: list[dict] = field(default_factory=list)
