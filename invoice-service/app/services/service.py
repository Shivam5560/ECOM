from __future__ import annotations

from invoice_service.schemas import Invoice


class InvoiceService:
    def generate(self, *, order_id: str, user_id: str, total: int) -> Invoice:
        return Invoice(
            order_id=order_id,
            user_id=user_id,
            total=total,
            created_by=user_id,
            receipt_html=f"<h1>Receipt</h1><p>Order {order_id}</p><strong>{total}</strong>",
        )
