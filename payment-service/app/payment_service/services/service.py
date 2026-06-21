from __future__ import annotations

from payment_service.schemas import Payment


class PaymentService:
    def __init__(self) -> None:
        self._payments_by_id: dict[str, Payment] = {}
        self._payments_by_idempotency: dict[str, Payment] = {}

    def authorize_cod(
        self,
        *,
        payment_id: str,
        order_id: str,
        amount: int,
        user_id: str,
        idempotency_key: str,
    ) -> Payment:
        existing = self._payments_by_idempotency.get(idempotency_key) or self._payments_by_id.get(payment_id)
        if existing is not None:
            return existing
        status = "failed" if amount <= 0 else "authorized"
        payment = Payment(
            id=payment_id,
            order_id=order_id,
            amount=amount,
            method="cod",
            status=status,
            user_id=user_id,
            idempotency_key=idempotency_key,
            created_by=user_id,
        )
        self._payments_by_id[payment_id] = payment
        self._payments_by_idempotency[idempotency_key] = payment
        return payment

    def list_payments(self) -> list[Payment]:
        return list(self._payments_by_id.values())


class SimulatedPaymentService(PaymentService):
    def authorize(self, *, order_id: str, amount: int, user_id: str) -> Payment:
        return self.authorize_cod(
            payment_id=f"pay-{order_id}",
            order_id=order_id,
            amount=amount,
            user_id=user_id,
            idempotency_key=f"pay-{order_id}",
        )
