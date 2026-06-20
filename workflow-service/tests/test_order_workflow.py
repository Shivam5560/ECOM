from __future__ import annotations

import asyncio
import unittest

from workflow_service.service import InMemoryOrderWorkflow


class OrderWorkflowTests(unittest.TestCase):
    def test_order_workflow_confirms_happy_path_and_emits_receipt_notification(self) -> None:
        async def scenario():
            workflow = InMemoryOrderWorkflow()
            return await workflow.start_checkout(
                order_id="order-1",
                user_id="buyer-1",
                lines=[{"product_id": "prod-1", "quantity": 1, "unit_price": 100}],
                correlation_id="corr-1",
            )

        result = asyncio.run(scenario())

        self.assertEqual(result.order_status, "confirmed")
        self.assertEqual(result.invoice["order_id"], "order-1")
        self.assertIn("invoice.generated", result.events)
        self.assertIn("notification.created", result.events)


if __name__ == "__main__":
    unittest.main()
