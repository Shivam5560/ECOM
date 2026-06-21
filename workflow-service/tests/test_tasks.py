from __future__ import annotations

import unittest

from core_common.exceptions import NotFoundError
from workflow_service.service import TaskCatalogService


class FakeTaskRepository:
    def __init__(self) -> None:
        self.tasks = {
            "checkout-confirmation": {
                "code": "checkout-confirmation",
                "name": "Checkout confirmation",
                "service": "notification-service",
                "status": "ready",
                "description": "Send customer and merchant confirmation after order confirmation.",
                "inputs": ["correlation_id"],
                "outputs": ["event"],
            }
        }

    def list(self) -> list[dict]:
        return list(self.tasks.values())

    def get(self, code: str) -> dict | None:
        return self.tasks.get(code)


class TaskCatalogServiceTests(unittest.TestCase):
    def test_lists_tasks_and_finds_detail_by_code_from_repository(self) -> None:
        service = TaskCatalogService(repo=FakeTaskRepository())

        all_tasks = service.list_tasks()
        task = service.get_task("checkout-confirmation")
        detail = service.get_task_detail("checkout-confirmation")

        self.assertEqual(len(all_tasks), 1)
        self.assertEqual(task["code"], "checkout-confirmation")
        self.assertIn("Send customer and merchant confirmation", detail["description"])

    def test_empty_repository_returns_blank_list_without_fallback_tasks(self) -> None:
        service = TaskCatalogService(repo=FakeTaskRepository())
        service._repo.tasks.clear()

        self.assertEqual(service.list_tasks(), [])
        with self.assertRaises(NotFoundError):
            service.get_task("checkout-confirmation")

    def test_database_url_or_repo_is_required(self) -> None:
        with self.assertRaises(RuntimeError):
            TaskCatalogService(database_url="")


if __name__ == "__main__":
    unittest.main()
