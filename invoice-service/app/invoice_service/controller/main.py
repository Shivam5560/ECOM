from __future__ import annotations

import dataclasses

from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from invoice_service.service import InvoiceService


def create_app():
    from fastapi import FastAPI, HTTPException

    app = FastAPI(title="invoice-service")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    service = InvoiceService()
    invoices: dict[str, tuple[object, bytes]] = {}

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/v1/invoices")
    async def generate_invoice(payload: dict) -> dict:
        invoice = service.generate(
            order_id=payload["order_id"],
            user_id=payload["user_id"],
            total=int(payload["total"]),
        )
        invoices[invoice.order_id] = (invoice, service.generate_pdf(invoice))
        return dataclasses.asdict(invoice)

    @app.get("/api/v1/invoices/{order_id}/pdf")
    async def download_invoice(order_id: str) -> Response:
        if order_id not in invoices:
            raise HTTPException(status_code=404, detail="invoice not found")
        _, pdf = invoices[order_id]
        return Response(content=pdf, media_type="application/pdf")

    return app
