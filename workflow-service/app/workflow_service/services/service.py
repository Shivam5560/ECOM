from __future__ import annotations

from dataclasses import dataclass
from os import getenv
from typing import Protocol

from core_common.exceptions import NotFoundError
from workflow_service.repo.repository import TaskRepository


@dataclass(frozen=True, slots=True)
class ConductorWorkflowStart:
    workflow_id: str
    workflow_name: str
    input: dict


class TaskRepo(Protocol):
    def list(self) -> list[dict]: ...
    def get(self, code: str) -> dict | None: ...


class TaskCatalogService:
    def __init__(self, database_url: str | None = None, *, repo: TaskRepo | None = None) -> None:
        if repo is not None:
            self._repo = repo
            return
        database_url = database_url if database_url is not None else getenv("WORKFLOW_DATABASE_URL")
        if not database_url:
            raise RuntimeError("WORKFLOW_DATABASE_URL is required for workflow task persistence")
        self._repo = TaskRepository(database_url)

    def init_resource(self, base_path: str = "/api/v1/tasks") -> dict:
        return {
            "resource": "tasks",
            "title": "Workflow Tasks",
            "columns": [
                {"key": "code", "label": "Code", "sortable": True},
                {"key": "name", "label": "Task", "sortable": True},
                {"key": "service", "label": "Service", "filterable": True},
                {"key": "status", "label": "Status", "filterable": True},
            ],
            "filters": [{"key": "service", "label": "Service"}],
            "links": {
                "list": base_path,
                "detail": f"{base_path}/{{code}}",
                "task_detail": f"{base_path}/{{code}}/detail",
            },
            "actions": {"view": f"{base_path}/{{code}}", "detail": f"{base_path}/{{code}}/detail"},
            "bulkActions": [],
        }

    def list_tasks(self) -> list[dict]:
        return self._repo.list()

    def get_task(self, code: str) -> dict:
        task = self._repo.get(code)
        if task is not None:
            return task
        raise NotFoundError("task not found")

    def get_task_detail(self, code: str) -> dict:
        task = self.get_task(code)
        task.setdefault("inputs", ["correlation_id", "order_id", "user_id"])
        task.setdefault("outputs", ["event", "status"])
        return task


class ConductorCheckoutStarter:
    workflow_name = "order_checkout_cod"

    def __init__(self) -> None:
        self._started_by_idempotency: dict[str, ConductorWorkflowStart] = {}

    def start_from_checkout_event(
        self,
        *,
        payload: dict,
        correlation_id: str,
        idempotency_key: str,
    ) -> ConductorWorkflowStart:
        existing = self._started_by_idempotency.get(idempotency_key)
        if existing is not None:
            return existing
        order_id = str(payload["order_id"])
        workflow_input = {
            "order_id": order_id,
            "user_id": payload["user_id"],
            "lines": payload["lines"],
            "total": payload["total"],
            "payment_method": payload["payment_method"],
            "correlation_id": correlation_id,
            "idempotency_key": idempotency_key,
            "reservation_id": f"res-{order_id}",
            "payment_id": f"pay-{order_id}",
        }
        started = ConductorWorkflowStart(
            workflow_id=f"checkout-{order_id}",
            workflow_name=self.workflow_name,
            input=workflow_input,
        )
        self._started_by_idempotency[idempotency_key] = started
        return started
