from __future__ import annotations
import dataclasses
from fastapi.middleware.cors import CORSMiddleware

from core_common.auth import get_current_user
from core_common.exceptions import AppError
from core_common.models import GridParams
from msg_common.bus import InMemoryEventBus
from order_service.service import OrderService


def create_app():
    from fastapi import FastAPI, Header, HTTPException

    app = FastAPI(title="order-service")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    service = OrderService(
        event_bus=InMemoryEventBus(source_service="order-service"),
    )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/v1/orders/init")
    async def gateway_init() -> dict:
        return service.init_resource("/api/v1/orders")

    @app.post("/api/v1/orders")
    async def create_order(payload: dict, authorization: str | None = Header(None)) -> dict:
        try:
            order = await service.create_order(
                current_user=await get_current_user(authorization),
                lines=payload["lines"],
                correlation_id=payload.get("correlation_id", "missing"),
                payment_method=payload["payment_method"],
            )
            return dataclasses.asdict(order)
        except AppError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    @app.get("/api/v1/orders")
    async def list_orders(page: int = 1, size: int = 20, status: str | None = None) -> dict:
        params = GridParams(page=page, size=size, filters={"status": status} if status else {})
        return dataclasses.asdict(service.list_orders(params))

    return app
