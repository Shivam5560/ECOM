from __future__ import annotations

import asyncio
import unittest
from os import getenv

from core_common.auth import CurrentUser
from core_common.exceptions import UnauthorizedError, ValidationError
from core_common.models import InMemoryRepository
from msg_common.bus import InMemoryEventBus
from order_service.repo.repository import OrderRepository
from order_service.schemas import Order
from order_service.service import OrderService


class FakeProductCatalog:
    def __init__(self) -> None:
        self.products = {
            "aurora-speaker": {
                "id": "aurora-speaker",
                "name": "Aurora Speaker",
                "stock": 8,
                "price": 249,
            },
            "halo-lamp": {
                "id": "halo-lamp",
                "name": "Halo Task Lamp",
                "stock": 11,
                "price": 164,
            },
        }

    async def get_product(self, product_id: str) -> dict[str, int | str]:
        return self.products[product_id]


class OrderCheckoutTests(unittest.TestCase):
    def service(self) -> OrderService:
        return OrderService(
            event_bus=InMemoryEventBus(source_service="order-service"),
            repo=InMemoryRepository[Order](),
        )

    def test_init_returns_gateway_links_for_order_screen(self) -> None:
        service = self.service()

        init = service.init_resource("/api/v1/orders")

        self.assertEqual(init["resource"], "orders")
        self.assertEqual(init["links"]["list"], "/api/v1/orders")
        self.assertEqual(init["links"]["create"], "/api/v1/orders")
        self.assertEqual(init["actions"]["cancel"], "/api/v1/orders/{id}/cancel")

    def test_create_order_reprices_lines_from_product_catalog(self) -> None:
        async def scenario():
            event_bus = InMemoryEventBus(source_service="order-service")
            service = OrderService(
                event_bus=event_bus,
                product_catalog=FakeProductCatalog(),
                repo=InMemoryRepository[Order](),
            )
            order = await service.create_order(
                current_user=CurrentUser(sub="buyer-1", email="buyer@ecom.dev", roles=["customer"]),
                lines=[
                    {"product_id": "aurora-speaker", "quantity": 2, "unit_price": 1},
                    {"product_id": "halo-lamp", "quantity": 1, "unit_price": 1},
                ],
                correlation_id="corr-1",
                payment_method="cod",
            )
            return order, event_bus.published

        order, events = asyncio.run(scenario())

        self.assertEqual(order.total, 662)
        self.assertEqual(order.status, "pending")
        self.assertEqual(order.lines[0]["unit_price"], 249)
        self.assertEqual(events[0].event_type, "order.checkout.requested")
        self.assertEqual(events[0].payload["payment_method"], "cod")
        self.assertEqual(events[0].idempotency_key, f"checkout-{order.id}")

    def test_create_order_requires_supported_payment_method(self) -> None:
        async def scenario():
            service = self.service()
            return await service.create_order(
                current_user=CurrentUser(sub="buyer-1", email="buyer@ecom.dev", roles=["customer"]),
                lines=[{"product_id": "aurora-speaker", "quantity": 1}],
                correlation_id="corr-1",
                payment_method="card",
            )

        with self.assertRaises(ValidationError):
            asyncio.run(scenario())

    def test_create_order_requires_authenticated_user(self) -> None:
        async def scenario():
            service = self.service()
            return await service.create_order(current_user=None, lines=[], correlation_id="corr-1", payment_method="cod")

        with self.assertRaises(UnauthorizedError):
            asyncio.run(scenario())

    @unittest.skipUnless(getenv("ORDER_TEST_DATABASE_URL"), "ORDER_TEST_DATABASE_URL is not configured")
    def test_repository_uses_order_test_database(self) -> None:
        async def scenario():
            service = OrderService(
                event_bus=InMemoryEventBus(source_service="order-service"),
                product_catalog=FakeProductCatalog(),
                repo=OrderRepository(getenv("ORDER_TEST_DATABASE_URL", "")),
            )
            return await service.create_order(
                current_user=CurrentUser(sub="buyer-1", email="buyer@ecom.dev"),
                lines=[{"product_id": "aurora-speaker", "quantity": 1}],
                correlation_id="corr-1",
                payment_method="cod",
            )

        order = asyncio.run(scenario())

        self.assertEqual(order.user_id, "buyer-1")


if __name__ == "__main__":
    unittest.main()
