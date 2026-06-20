from __future__ import annotations

from payment_service.schemas import Payment


class SimulatedPaymentService:
    def authorize(self, *, order_id: str, amount: int, user_id: str) -> Payment:
        status = "failed" if amount <= 0 else "authorized"
        return Payment(order_id=order_id, amount=amount, status=status, created_by=user_id)
