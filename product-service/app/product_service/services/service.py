from __future__ import annotations

from os import getenv
from typing import Any, Protocol

from core_common.auth import CurrentUser
from core_common.exceptions import ForbiddenError, NotFoundError, ValidationError
from core_common.models import GridColumn, GridParams, PagedResponse

from product_service.repo.repository import ProductRepository
from product_service.schemas import (
    OrderReservationResult,
    Product,
    ReservationCommitResult,
    ReservationReleaseResult,
    ReservationResult,
)

class ProductRepo(Protocol):
    def add(self, product: Product) -> Product: ...
    def get(self, product_id: str) -> Product | None: ...
    def soft_delete(self, product_id: str, *, deleted_by: str | None = None) -> Product | None: ...
    def list(
        self,
        params: GridParams | None = None,
        *,
        columns: list[GridColumn] | None = None,
        actions: list[dict[str, Any]] | None = None,
    ) -> PagedResponse[Product]: ...


class ProductCatalogService:
    def __init__(self, database_url: str | None = None, *, repo: ProductRepo | None = None) -> None:
        if repo is not None:
            self.repo = repo
            self._reservations: dict[str, dict[str, Any]] = {}
            return
        database_url = database_url if database_url is not None else getenv("PRODUCT_DATABASE_URL")
        if not database_url:
            raise RuntimeError("PRODUCT_DATABASE_URL is required for product persistence")
        self.repo = ProductRepository(database_url)
        self._reservations: dict[str, dict[str, Any]] = {}

    def init_resource(self, base_path: str = "/api/v1/products") -> dict[str, Any]:
        return {
            "resource": "products",
            "title": "Products",
            "columns": [
                {"key": "name", "label": "Product", "sortable": True, "filterable": True},
                {"key": "category", "label": "Category", "sortable": True, "filterable": True},
                {"key": "price", "label": "Price", "kind": "currency", "sortable": True},
                {"key": "stock", "label": "Stock", "kind": "number", "sortable": True},
                {"key": "rating", "label": "Rating", "kind": "number", "sortable": True},
            ],
            "filters": [{"key": "category", "label": "Category"}],
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
                "create": base_path,
                "update": f"{base_path}/{{id}}",
                "delete": f"{base_path}/{{id}}",
            },
            "bulkActions": ["bulk_create", "bulk_delete"],
        }

    def list_products(self, params: GridParams | None = None) -> PagedResponse[Product]:
        return self.repo.list(
            params or GridParams(),
            columns=[
                GridColumn("name", "Product", filterable=True),
                GridColumn("category", "Category", filterable=True),
                GridColumn("price", "Price", kind="currency"),
                GridColumn("stock", "Stock", kind="number"),
            ],
            actions=[{"key": "view", "label": "View"}, {"key": "reserve", "label": "Reserve"}],
        )

    def get_product(self, product_id: str) -> Product:
        product = self.repo.get(product_id)
        if product is None:
            raise NotFoundError("product not found")
        return product

    def create_products(
        self,
        payload: dict[str, Any] | list[dict[str, Any]],
        *,
        current_user: CurrentUser,
    ) -> list[Product]:
        self._require_admin(current_user)
        rows = payload if isinstance(payload, list) else [payload]
        created: list[Product] = []
        for row in rows:
            product = self._product_from_payload(row, created_by=current_user.sub)
            self.repo.add(product)
            created.append(product)
        return created

    def update_product(
        self,
        product_id: str,
        payload: dict[str, Any],
        *,
        current_user: CurrentUser,
    ) -> Product:
        self._require_admin(current_user)
        product = self.get_product(product_id)
        for key in ("name", "category", "description", "price", "stock", "rating", "image", "accent"):
            if key in payload:
                setattr(product, key, payload[key])
        product.touch(current_user.sub)
        self.repo.add(product)
        return product

    def delete_products(
        self,
        ids: str | list[str],
        *,
        current_user: CurrentUser,
    ) -> dict[str, list[str]]:
        self._require_admin(current_user)
        product_ids = [ids] if isinstance(ids, str) else ids
        deleted: list[str] = []
        missing: list[str] = []
        for product_id in product_ids:
            if self.repo.soft_delete(product_id, deleted_by=current_user.sub) is None:
                missing.append(product_id)
            else:
                deleted.append(product_id)
        return {"deleted": deleted, "missing": missing}

    def reserve(self, product_id: str, quantity: int) -> ReservationResult:
        product = self.repo.get(product_id)
        if product is None or product.stock < quantity:
            return ReservationResult(product_id=product_id, quantity=quantity, reserved=False)
        product.stock -= quantity
        product.touch("workflow-service")
        self.repo.add(product)
        return ReservationResult(product_id=product_id, quantity=quantity, reserved=True)

    def reserve_order(self, *, reservation_id: str, order_id: str, lines: list[dict]) -> OrderReservationResult:
        existing = self._reservations.get(reservation_id)
        if existing is not None:
            return OrderReservationResult(
                reservation_id=reservation_id,
                order_id=str(existing["order_id"]),
                reserved=existing["status"] in {"reserved", "committed", "released"},
                lines=list(existing["lines"]),
                reason=str(existing.get("reason", "")),
            )

        normalized = self._normalize_lines(lines)
        products: dict[str, Product] = {}
        for line in normalized:
            product = self.repo.get(line["product_id"])
            if product is None:
                return self._record_rejected(reservation_id, order_id, normalized, "product not found")
            if product.stock < line["quantity"]:
                return self._record_rejected(reservation_id, order_id, normalized, "insufficient stock")
            products[line["product_id"]] = product

        for line in normalized:
            product = products[line["product_id"]]
            product.stock -= line["quantity"]
            product.touch("workflow-service")
            self.repo.add(product)

        self._reservations[reservation_id] = {
            "order_id": order_id,
            "lines": normalized,
            "status": "reserved",
            "reason": "",
        }
        return OrderReservationResult(
            reservation_id=reservation_id,
            order_id=order_id,
            reserved=True,
            lines=normalized,
        )

    def commit_reservation(self, reservation_id: str) -> ReservationCommitResult:
        reservation = self._reservations.get(reservation_id)
        if reservation is None:
            return ReservationCommitResult(reservation_id=reservation_id, committed=False)
        if reservation["status"] == "released":
            return ReservationCommitResult(reservation_id=reservation_id, committed=False)
        reservation["status"] = "committed"
        return ReservationCommitResult(reservation_id=reservation_id, committed=True)

    def release_reservation(self, reservation_id: str) -> ReservationReleaseResult:
        reservation = self._reservations.get(reservation_id)
        if reservation is None:
            return ReservationReleaseResult(reservation_id=reservation_id, released=False)
        if reservation["status"] == "released":
            return ReservationReleaseResult(reservation_id=reservation_id, released=True)
        if reservation["status"] == "committed":
            return ReservationReleaseResult(reservation_id=reservation_id, released=False)
        for line in reservation["lines"]:
            product = self.repo.get(line["product_id"])
            if product is not None:
                product.stock += line["quantity"]
                product.touch("workflow-service")
                self.repo.add(product)
        reservation["status"] = "released"
        return ReservationReleaseResult(reservation_id=reservation_id, released=True)

    def _normalize_lines(self, lines: list[dict]) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        for line in lines:
            quantity = int(line.get("quantity", 0))
            if quantity <= 0:
                raise ValidationError("reservation line quantity must be positive")
            normalized.append({"product_id": str(line["product_id"]), "quantity": quantity})
        return normalized

    def _record_rejected(
        self,
        reservation_id: str,
        order_id: str,
        lines: list[dict[str, Any]],
        reason: str,
    ) -> OrderReservationResult:
        self._reservations[reservation_id] = {
            "order_id": order_id,
            "lines": lines,
            "status": "rejected",
            "reason": reason,
        }
        return OrderReservationResult(
            reservation_id=reservation_id,
            order_id=order_id,
            reserved=False,
            lines=lines,
            reason=reason,
        )

    def _require_admin(self, current_user: CurrentUser) -> None:
        if "admin" not in current_user.roles:
            raise ForbiddenError("admin role required")

    def _product_from_payload(self, payload: dict[str, Any], *, created_by: str) -> Product:
        if not payload.get("name"):
            raise ValidationError("product name is required")
        if not payload.get("category"):
            raise ValidationError("product category is required")
        product = Product(
            name=payload["name"],
            category=payload["category"],
            description=payload.get("description", ""),
            price=int(payload.get("price", 0)),
            stock=int(payload.get("stock", payload.get("quantity", 0))),
            rating=float(payload.get("rating", 4.5)),
            image=payload.get("image", ""),
            accent=payload.get("accent", "#0e5d4e"),
            created_by=created_by,
        )
        if payload.get("id"):
            product.id = str(payload["id"])
        return product
