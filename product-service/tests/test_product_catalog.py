from __future__ import annotations

import unittest
from os import getenv
from uuid import uuid4

from core_common.auth import CurrentUser
from core_common.exceptions import ForbiddenError, NotFoundError
from core_common.models import InMemoryRepository
from product_service.repo.repository import ProductRepository
from product_service.service import ProductCatalogService
from product_service.schemas import Product


def service_with_repo() -> ProductCatalogService:
    return ProductCatalogService(repo=InMemoryRepository[Product]())


class ProductCatalogServiceTests(unittest.TestCase):
    def test_init_returns_gateway_links_for_all_crud_actions(self) -> None:
        service = service_with_repo()

        init = service.init_resource("/api/v1/products")

        self.assertEqual(init["resource"], "products")
        self.assertEqual(init["links"]["list"], "/api/v1/products")
        self.assertEqual(init["links"]["create"], "/api/v1/products")
        self.assertEqual(init["links"]["bulk_delete"], "/api/v1/products")
        self.assertIn("bulk_create", init["bulkActions"])
        self.assertIn("delete", init["actions"])

    def test_catalog_is_empty_without_scripted_data(self) -> None:
        service = service_with_repo()

        page = service.list_products()

        self.assertEqual(page.items, [])
        self.assertEqual(page.total, 0)

    def test_database_url_or_repo_is_required(self) -> None:
        with self.assertRaises(RuntimeError):
            ProductCatalogService(database_url="")

    def test_admin_can_bulk_create_and_customer_cannot(self) -> None:
        service = service_with_repo()
        admin = CurrentUser(sub="admin-1", email="admin@ecom.dev", roles=["admin"])
        customer = CurrentUser(sub="buyer-1", email="buyer@ecom.dev", roles=["customer"])

        created = service.create_products(
            [
                {
                    "id": "linen-shirt",
                    "name": "Linen Utility Shirt",
                    "category": "Wear",
                    "description": "Breathable everyday shirt",
                    "price": 98,
                    "stock": 12,
                    "rating": 4.6,
                    "image": "/images/linen-shirt.jpg",
                    "accent": "#7c8a62",
                }
            ],
            current_user=admin,
        )

        self.assertEqual(len(created), 1)
        self.assertEqual(service.get_product("linen-shirt").name, "Linen Utility Shirt")
        with self.assertRaises(ForbiddenError):
            service.create_products(
                [{"id": "blocked", "name": "Blocked", "category": "Desk", "price": 10}],
                current_user=customer,
            )

    def test_admin_can_update_and_bulk_delete_products(self) -> None:
        service = service_with_repo()
        admin = CurrentUser(sub="admin-1", email="admin@ecom.dev", roles=["admin"])
        service.create_products(
            {
                "id": "aurora-speaker",
                "name": "Aurora Speaker",
                "category": "Audio",
                "description": "Portable room speaker",
                "price": 249,
                "stock": 8,
            },
            current_user=admin,
        )

        updated = service.update_product(
            "aurora-speaker",
            {"price": 229, "stock": 6},
            current_user=admin,
        )
        deleted = service.delete_products(["aurora-speaker", "missing"], current_user=admin)

        self.assertEqual(updated.price, 229)
        self.assertEqual(deleted["deleted"], ["aurora-speaker"])
        self.assertEqual(deleted["missing"], ["missing"])
        with self.assertRaises(NotFoundError):
            service.get_product("aurora-speaker")

    def test_checkout_reservation_prevents_overselling_last_stock_unit(self) -> None:
        service = service_with_repo()
        admin = CurrentUser(sub="admin-1", email="admin@ecom.dev", roles=["admin"])
        service.create_products(
            {
                "id": "last-unit",
                "name": "Last Unit",
                "category": "Limited",
                "price": 100,
                "stock": 1,
            },
            current_user=admin,
        )

        first = service.reserve_order(
            reservation_id="res-order-1",
            order_id="order-1",
            lines=[{"product_id": "last-unit", "quantity": 1}],
        )
        duplicate = service.reserve_order(
            reservation_id="res-order-1",
            order_id="order-1",
            lines=[{"product_id": "last-unit", "quantity": 1}],
        )
        second = service.reserve_order(
            reservation_id="res-order-2",
            order_id="order-2",
            lines=[{"product_id": "last-unit", "quantity": 1}],
        )

        self.assertTrue(first.reserved)
        self.assertTrue(duplicate.reserved)
        self.assertFalse(second.reserved)
        self.assertEqual(service.get_product("last-unit").stock, 0)

    def test_releasing_reservation_returns_stock_once(self) -> None:
        service = service_with_repo()
        admin = CurrentUser(sub="admin-1", email="admin@ecom.dev", roles=["admin"])
        service.create_products(
            {
                "id": "release-me",
                "name": "Release Me",
                "category": "Limited",
                "price": 100,
                "stock": 1,
            },
            current_user=admin,
        )
        service.reserve_order(
            reservation_id="res-order-1",
            order_id="order-1",
            lines=[{"product_id": "release-me", "quantity": 1}],
        )

        released = service.release_reservation("res-order-1")
        duplicate = service.release_reservation("res-order-1")

        self.assertTrue(released.released)
        self.assertTrue(duplicate.released)
        self.assertEqual(service.get_product("release-me").stock, 1)

    def test_committing_reservation_keeps_stock_decremented(self) -> None:
        service = service_with_repo()
        admin = CurrentUser(sub="admin-1", email="admin@ecom.dev", roles=["admin"])
        service.create_products(
            {
                "id": "commit-me",
                "name": "Commit Me",
                "category": "Limited",
                "price": 100,
                "stock": 1,
            },
            current_user=admin,
        )
        service.reserve_order(
            reservation_id="res-order-1",
            order_id="order-1",
            lines=[{"product_id": "commit-me", "quantity": 1}],
        )

        committed = service.commit_reservation("res-order-1")
        duplicate = service.commit_reservation("res-order-1")

        self.assertTrue(committed.committed)
        self.assertTrue(duplicate.committed)
        self.assertEqual(service.get_product("commit-me").stock, 0)

    @unittest.skipUnless(getenv("PRODUCT_TEST_DATABASE_URL"), "PRODUCT_TEST_DATABASE_URL is not configured")
    def test_repository_uses_product_test_database(self) -> None:
        repo = ProductRepository(getenv("PRODUCT_TEST_DATABASE_URL", ""))
        service = ProductCatalogService(repo=repo)
        admin = CurrentUser(sub="admin-1", email="admin@ecom.dev", roles=["admin"])
        product_id = f"test-{uuid4()}"

        service.create_products(
            {
                "id": product_id,
                "name": "Integration Product",
                "category": "Test",
                "price": 10,
                "stock": 1,
            },
            current_user=admin,
        )

        self.assertEqual(service.get_product(product_id).name, "Integration Product")
        service.delete_products(product_id, current_user=admin)


if __name__ == "__main__":
    unittest.main()
