from __future__ import annotations

from dataclasses import dataclass

from core_common.models import AuditEntity


@dataclass(slots=True)
class Invoice(AuditEntity):
    order_id: str = ""
    user_id: str = ""
    total: int = 0
    receipt_html: str = ""
