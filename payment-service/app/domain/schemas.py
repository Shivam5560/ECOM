from __future__ import annotations

from dataclasses import dataclass

from core_common.models import AuditEntity


@dataclass(slots=True)
class Payment(AuditEntity):
    order_id: str = ""
    amount: int = 0
    status: str = "authorized"
