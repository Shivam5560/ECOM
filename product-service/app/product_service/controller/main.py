from __future__ import annotations
import dataclasses
from typing import Any

from fastapi.middleware.cors import CORSMiddleware

from core_common.auth import get_current_user
from core_common.exceptions import AppError
from core_common.models import GridParams
from product_service.service import ProductCatalogService


def _asdict(value: Any) -> Any:
    if dataclasses.is_dataclass(value):
        return dataclasses.asdict(value)
    if isinstance(value, list):
        return [_asdict(item) for item in value]
    return value


def create_app():
    from fastapi import FastAPI, Header, HTTPException

    app = FastAPI(title="product-service")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    service = ProductCatalogService()

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/v1/products/init")
    async def gateway_init() -> dict:
        return service.init_resource("/api/v1/products")

    @app.get("/api/v1/products")
    async def list_products(page: int = 1, size: int = 20, category: str | None = None) -> dict:
        params = GridParams(page=page, size=size, filters={"category": category} if category else {})
        return dataclasses.asdict(service.list_products(params))

    @app.get("/api/v1/products/{product_id}")
    async def get_product(product_id: str) -> dict:
        try:
            return dataclasses.asdict(service.get_product(product_id))
        except AppError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    @app.post("/api/v1/products")
    async def create_products(payload: dict | list[dict], authorization: str | None = Header(None)) -> dict:
        try:
            created = service.create_products(payload, current_user=await get_current_user(authorization))
            return {"items": _asdict(created), "total": len(created)}
        except AppError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    @app.patch("/api/v1/products/{product_id}")
    async def update_product(product_id: str, payload: dict, authorization: str | None = Header(None)) -> dict:
        try:
            return dataclasses.asdict(
                service.update_product(product_id, payload, current_user=await get_current_user(authorization))
            )
        except AppError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    @app.delete("/api/v1/products/{product_id}")
    async def delete_product(product_id: str, authorization: str | None = Header(None)) -> dict:
        try:
            return service.delete_products(product_id, current_user=await get_current_user(authorization))
        except AppError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    @app.delete("/api/v1/products")
    async def bulk_delete_products(payload: dict, authorization: str | None = Header(None)) -> dict:
        try:
            return service.delete_products(payload.get("ids", []), current_user=await get_current_user(authorization))
        except AppError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    @app.post("/api/v1/inventory/reservations")
    async def reserve_inventory(payload: dict) -> dict:
        try:
            return dataclasses.asdict(
                service.reserve_order(
                    reservation_id=payload["reservation_id"],
                    order_id=payload["order_id"],
                    lines=payload["lines"],
                )
            )
        except AppError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    @app.post("/api/v1/inventory/reservations/{reservation_id}/commit")
    async def commit_inventory(reservation_id: str) -> dict:
        return dataclasses.asdict(service.commit_reservation(reservation_id))

    @app.post("/api/v1/inventory/reservations/{reservation_id}/release")
    async def release_inventory(reservation_id: str) -> dict:
        return dataclasses.asdict(service.release_reservation(reservation_id))

    return app
