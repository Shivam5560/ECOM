from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class WorkflowResult:
    order_id: str
    order_status: str
    events: list[str]
    invoice: dict
    notification: dict
