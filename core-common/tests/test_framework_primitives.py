from __future__ import annotations

import asyncio
import unittest

from core_common.models import AuditEntity, GridColumn, GridParams, InMemoryRepository
from core_common.cache import InMemoryCacheBackend, cacheable


class FrameworkPrimitiveTests(unittest.TestCase):
    def test_audit_entity_soft_delete_marks_deleted_metadata(self) -> None:
        entity = AuditEntity(created_by="buyer-1")

        entity.soft_delete("admin-1")

        self.assertFalse(entity.is_active)
        self.assertIsNotNone(entity.deleted_at)
        self.assertEqual(entity.deleted_by, "admin-1")

    def test_repository_list_excludes_soft_deleted_and_returns_grid_metadata(self) -> None:
        repo = InMemoryRepository[AuditEntity]()
        active = AuditEntity(created_by="buyer-1")
        deleted = AuditEntity(created_by="buyer-2")
        repo.add(active)
        repo.add(deleted)
        repo.soft_delete(deleted.id, deleted_by="admin-1")

        result = repo.list(GridParams(page=1, size=10), columns=[GridColumn(key="id", label="ID")])

        self.assertEqual(result.total, 1)
        self.assertEqual(result.items, [active])
        self.assertEqual(result.columns[0].key, "id")
        self.assertEqual(result.actions[0]["key"], "view")

    def test_cacheable_reuses_value_until_invalidated(self) -> None:
        async def scenario() -> tuple[int, int, int]:
            backend = InMemoryCacheBackend()
            calls = {"count": 0}

            @cacheable(backend=backend, ttl_seconds=60, key_prefix="demo")
            async def load_value(name: str) -> int:
                calls["count"] += 1
                return len(name) + calls["count"]

            first = await load_value("cart")
            second = await load_value("cart")
            backend.invalidate_prefix("demo")
            third = await load_value("cart")
            return first, second, third

        first, second, third = asyncio.run(scenario())
        self.assertEqual(first, second)
        self.assertNotEqual(second, third)


if __name__ == "__main__":
    unittest.main()
