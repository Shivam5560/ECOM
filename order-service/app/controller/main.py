from __future__ import annotations

from core_common.models import GridParams
from msg_common.bus import InMemoryEventBus
from order_service.service import OrderService


def create_app():
    from fastapi import FastAPI

    app = FastAPI(title="order-service")
    service = OrderService(event_bus=InMemoryEventBus(source_service="order-service"))

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/orders")
    async def create_order(payload: dict) -> dict:
        order = await service.create_order(
            user_id=payload["user_id"],
            lines=payload["lines"],
            correlation_id=payload.get("correlation_id", "missing"),
        )
        return order.__dict__

    @app.get("/orders")
    async def list_orders(page: int = 1, size: int = 20, status: str | None = None) -> dict:
        params = GridParams(page=page, size=size, filters={"status": status} if status else {})
        return service.list_orders(params).__dict__

    return app
