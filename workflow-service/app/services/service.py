from __future__ import annotations

from workflow_service.schemas import WorkflowResult


class InMemoryOrderWorkflow:
    async def start_checkout(
        self,
        *,
        order_id: str,
        user_id: str,
        lines: list[dict],
        correlation_id: str,
    ) -> WorkflowResult:
        total = sum(line["quantity"] * line["unit_price"] for line in lines)
        events = [
            "order.checkout.requested",
            "inventory.reserve.requested",
            "inventory.reserved",
            "payment.authorize.requested",
            "payment.authorized",
            "invoice.generate.requested",
            "invoice.generated",
            "notification.created",
            "order.confirmed",
        ]
        invoice = {
            "invoice_id": f"inv-{order_id}",
            "order_id": order_id,
            "user_id": user_id,
            "total": total,
            "receipt_url": f"/orders/{order_id}/receipt",
        }
        notification = {
            "user_id": user_id,
            "type": "order.confirmed",
            "message": f"Order {order_id} confirmed",
            "correlation_id": correlation_id,
        }
        return WorkflowResult(
            order_id=order_id,
            order_status="confirmed",
            events=events,
            invoice=invoice,
            notification=notification,
        )
