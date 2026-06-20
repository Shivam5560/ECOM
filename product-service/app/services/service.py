from __future__ import annotations

from core_common.models import GridColumn, GridParams, InMemoryRepository, PagedResponse

from product_service.schemas import Product, ReservationResult


class ProductCatalogService:
    def __init__(self) -> None:
        self.repo = InMemoryRepository[Product]()
        for product in [
            Product(id="aurora-speaker", name="Aurora Speaker", category="Audio", price=249, stock=8),
            Product(id="linea-tote", name="Linea Carry Tote", category="Carry", price=188, stock=5),
            Product(id="halo-lamp", name="Halo Task Lamp", category="Desk", price=164, stock=11),
        ]:
            self.repo.add(product)

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

    def reserve(self, product_id: str, quantity: int) -> ReservationResult:
        product = self.repo.get(product_id)
        if product is None or product.stock < quantity:
            return ReservationResult(product_id=product_id, quantity=quantity, reserved=False)
        product.stock -= quantity
        product.touch("workflow-service")
        return ReservationResult(product_id=product_id, quantity=quantity, reserved=True)
