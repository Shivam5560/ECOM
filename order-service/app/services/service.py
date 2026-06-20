from __future__ import annotations

from core_common.models import GridColumn, GridParams, InMemoryRepository, PagedResponse
from msg_common.bus import EventBus

from order_service.schemas import Order


class OrderService:
    def __init__(self, *, event_bus: EventBus) -> None:
        self.event_bus = event_bus
        self.repo = InMemoryRepository[Order]()

    async def create_order(self, *, user_id: str, lines: list[dict], correlation_id: str) -> Order:
        total = sum(line["quantity"] * line["unit_price"] for line in lines)
        order = self.repo.add(Order(user_id=user_id, lines=lines, total=total, created_by=user_id))
        await self.event_bus.publish(
            event_type="order.checkout.requested",
            payload={"order_id": order.id, "user_id": user_id, "lines": lines, "total": total},
            correlation_id=correlation_id,
        )
        return order

    def list_orders(self, params: GridParams | None = None) -> PagedResponse[Order]:
        return self.repo.list(
            params or GridParams(),
            columns=[
                GridColumn("id", "Order"),
                GridColumn("status", "Status", filterable=True),
                GridColumn("total", "Total", kind="currency"),
                GridColumn("created_at", "Created", kind="datetime"),
            ],
            actions=[{"key": "view", "label": "View"}, {"key": "receipt", "label": "Receipt"}],
        )
