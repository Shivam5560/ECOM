from __future__ import annotations
import dataclasses
from fastapi.middleware.cors import CORSMiddleware

from core_common.exceptions import AppError
from workflow_service.service import ConductorCheckoutStarter, TaskCatalogService


def create_app():
    from fastapi import FastAPI

    app = FastAPI(title="workflow-service")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    conductor = ConductorCheckoutStarter()
    tasks = TaskCatalogService()

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/v1/tasks/init")
    async def task_init() -> dict:
        return tasks.init_resource("/api/v1/tasks")

    @app.get("/api/v1/tasks")
    async def list_tasks() -> list[dict]:
        return tasks.list_tasks()

    @app.get("/api/v1/tasks/{code}")
    async def get_task(code: str) -> dict:
        from fastapi import HTTPException

        try:
            return tasks.get_task(code)
        except AppError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    @app.get("/api/v1/tasks/{code}/detail")
    async def get_task_detail(code: str) -> dict:
        from fastapi import HTTPException

        try:
            return tasks.get_task_detail(code)
        except AppError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    @app.post("/api/v1/workflows/order-checkout/start")
    async def start_conductor_checkout(payload: dict) -> dict:
        started = conductor.start_from_checkout_event(
            payload=payload["payload"],
            correlation_id=payload["correlation_id"],
            idempotency_key=payload["idempotency_key"],
        )
        return dataclasses.asdict(started)

    return app
