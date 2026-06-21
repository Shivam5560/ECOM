from __future__ import annotations

import inspect
from os import getenv
from typing import Any, Protocol

from core_common.auth import CurrentUser
from core_common.exceptions import UnauthorizedError, ValidationError
from core_common.models import GridColumn, GridParams, PagedResponse
from msg_common.bus import DomainRouting, EventBus

from order_service.repo.repository import OrderRepository
from order_service.schemas import Order

try:
    import httpx
except ModuleNotFoundError:
    httpx = None


class OrderRepo(Protocol):
    def add(self, order: Order) -> Order: ...
    def list(
        self,
        params: GridParams | None = None,
        *,
        columns: list[GridColumn] | None = None,
        actions: list[dict[str, Any]] | None = None,
    ) -> PagedResponse[Order]: ...


class RemoteProductCatalog:
    def __init__(self, base_url: str) -> None:
        if httpx is None:
            raise RuntimeError("httpx is required when PRODUCT_SERVICE_URL is configured")
        self.base_url = base_url.rstrip("/")

    async def get_product(self, product_id: str) -> dict[str, Any]:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=10.0) as client:
            response = await client.get(f"/api/v1/products/{product_id}")
            response.raise_for_status()
            payload = response.json()
        if isinstance(payload, dict) and "data" in payload and isinstance(payload["data"], dict):
            return payload["data"]
        if not isinstance(payload, dict):
            raise ValidationError("product catalog returned an invalid response")
        return payload


class OrderService:
    def __init__(
        self,
        *,
        event_bus: EventBus,
        product_catalog: Any | None = None,
        database_url: str | None = None,
        repo: OrderRepo | None = None,
    ) -> None:
        self.event_bus = event_bus
        self.product_catalog = product_catalog or self._default_product_catalog()
        if repo is not None:
            self.repo = repo
            return
        database_url = database_url if database_url is not None else getenv("ORDER_DATABASE_URL")
        if not database_url:
            raise RuntimeError("ORDER_DATABASE_URL is required for order persistence")
        self.repo = OrderRepository(database_url)

    def init_resource(self, base_path: str = "/api/v1/orders") -> dict[str, Any]:
        return {
            "resource": "orders",
            "title": "Orders",
            "columns": [
                {"key": "id", "label": "Order", "sortable": True},
                {"key": "status", "label": "Status", "sortable": True, "filterable": True},
                {"key": "total", "label": "Total", "kind": "currency", "sortable": True},
                {"key": "created_at", "label": "Created", "kind": "datetime", "sortable": True},
            ],
            "filters": [{"key": "status", "label": "Status"}],
            "links": {
                "list": base_path,
                "detail": f"{base_path}/{{id}}",
                "create": base_path,
                "update": f"{base_path}/{{id}}",
                "delete": f"{base_path}/{{id}}",
                "bulk_create": base_path,
                "bulk_delete": base_path,
            },
            "actions": {
                "view": f"{base_path}/{{id}}",
                "cancel": f"{base_path}/{{id}}/cancel",
                "invoice": f"{base_path}/{{id}}/invoice",
            },
            "bulkActions": [],
        }

    async def create_order(
        self,
        *,
        current_user: CurrentUser | None,
        lines: list[dict],
        correlation_id: str,
        payment_method: str,
    ) -> Order:
        if current_user is None:
            raise UnauthorizedError("checkout requires authentication")
        if payment_method != "cod":
            raise ValidationError("payment method is not available")
        priced_lines = await self._price_lines(lines)
        total = sum(line["quantity"] * line["unit_price"] for line in priced_lines)
        order = self.repo.add(
            Order(
                user_id=current_user.sub,
                lines=priced_lines,
                total=total,
                created_by=current_user.sub,
            )
        )
        await self.event_bus.publish(
            event_type=DomainRouting.order_checkout_requested,
            payload={
                "order_id": order.id,
                "user_id": current_user.sub,
                "lines": priced_lines,
                "total": total,
                "payment_method": payment_method,
            },
            correlation_id=correlation_id,
            idempotency_key=f"checkout-{order.id}",
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

    async def _price_lines(self, lines: list[dict]) -> list[dict]:
        priced: list[dict] = []
        for line in lines:
            quantity = int(line.get("quantity", 0))
            if quantity <= 0:
                raise ValidationError("order line quantity must be positive")
            if self.product_catalog is None:
                raise ValidationError("product catalog is required to price checkout lines")
            product = self.product_catalog.get_product(line["product_id"])
            if inspect.isawaitable(product):
                product = await product
            product_id = product["id"] if isinstance(product, dict) else product.id
            stock = product["stock"] if isinstance(product, dict) else product.stock
            unit_price = product["price"] if isinstance(product, dict) else product.price
            name = product["name"] if isinstance(product, dict) else product.name
            if stock < quantity:
                raise ValidationError("insufficient product stock")
            priced.append(
                {
                    "product_id": product_id,
                    "name": name,
                    "quantity": quantity,
                    "unit_price": unit_price,
                }
            )
        return priced

    def _default_product_catalog(self) -> Any | None:
        base_url = getenv("PRODUCT_SERVICE_URL")
        if not base_url:
            return None
        return RemoteProductCatalog(base_url)
