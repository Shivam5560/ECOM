from __future__ import annotations

import dataclasses

from fastapi.middleware.cors import CORSMiddleware

from payment_service.service import PaymentService


def create_app():
    from fastapi import FastAPI

    app = FastAPI(title="payment-service")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    service = PaymentService()

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/v1/payments/cod/authorize")
    async def authorize_cod(payload: dict) -> dict:
        payment = service.authorize_cod(
            payment_id=payload["payment_id"],
            order_id=payload["order_id"],
            amount=int(payload["amount"]),
            user_id=payload["user_id"],
            idempotency_key=payload["idempotency_key"],
        )
        return dataclasses.asdict(payment)

    @app.get("/api/v1/payments")
    async def list_payments() -> dict:
        items = [dataclasses.asdict(payment) for payment in service.list_payments()]
        return {"items": items, "total": len(items)}

    return app
