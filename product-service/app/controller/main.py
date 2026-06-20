from __future__ import annotations

from core_common.models import GridParams
from product_service.service import ProductCatalogService


def create_app():
    from fastapi import FastAPI

    app = FastAPI(title="product-service")
    service = ProductCatalogService()

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/products")
    async def list_products(page: int = 1, size: int = 20, category: str | None = None) -> dict:
        params = GridParams(page=page, size=size, filters={"category": category} if category else {})
        return service.list_products(params).__dict__

    return app
