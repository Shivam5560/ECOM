from __future__ import annotations

import unittest

from payment_service.service import PaymentService


class CodPaymentTests(unittest.TestCase):
    def test_authorizes_cod_payment_idempotently(self) -> None:
        service = PaymentService()

        first = service.authorize_cod(
            payment_id="pay-order-1",
            order_id="order-1",
            amount=249,
            user_id="buyer-1",
            idempotency_key="checkout-order-1",
        )
        duplicate = service.authorize_cod(
            payment_id="pay-order-1",
            order_id="order-1",
            amount=249,
            user_id="buyer-1",
            idempotency_key="checkout-order-1",
        )

        self.assertEqual(first.status, "authorized")
        self.assertEqual(first.method, "cod")
        self.assertEqual(first.id, duplicate.id)
        self.assertEqual(len(service.list_payments()), 1)

    def test_rejects_non_positive_cod_amount(self) -> None:
        service = PaymentService()

        payment = service.authorize_cod(
            payment_id="pay-order-1",
            order_id="order-1",
            amount=0,
            user_id="buyer-1",
            idempotency_key="checkout-order-1",
        )

        self.assertEqual(payment.status, "failed")


if __name__ == "__main__":
    unittest.main()
