from __future__ import annotations

from workflow_service.service import InMemoryOrderWorkflow


def create_app():
    from fastapi import FastAPI

    app = FastAPI(title="workflow-service")
    workflow = InMemoryOrderWorkflow()

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/workflows/order-checkout")
    async def start_checkout(payload: dict) -> dict:
        result = await workflow.start_checkout(
            order_id=payload["order_id"],
            user_id=payload["user_id"],
            lines=payload["lines"],
            correlation_id=payload.get("correlation_id", "missing"),
        )
        return result.__dict__

    return app
