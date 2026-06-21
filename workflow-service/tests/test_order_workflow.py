from __future__ import annotations

import asyncio
import json
import unittest
from pathlib import Path

from workflow_service.service import ConductorCheckoutStarter


class OrderWorkflowTests(unittest.TestCase):
    def test_order_workflow_definition_includes_post_confirmation_invoice_and_notification(self) -> None:
        workflow_path = Path(__file__).parents[1] / "app/workflow_service/workflows/order_checkout.json"
        workflow = json.loads(workflow_path.read_text())
        task_refs = [task["taskReferenceName"] for task in workflow["tasks"]]

        self.assertEqual(
            task_refs[:10],
            [
                "reserve_inventory",
                "inventory_reservation_boundary",
                "validate_cod_payment",
                "payment_validation_boundary",
                "authorize_cod_payment",
                "cod_authorization_boundary",
                "confirm_order",
                "order_confirmation_boundary",
                "commit_inventory",
                "inventory_commit_boundary",
            ],
        )
        self.assertIn("publish_order_confirmed", task_refs)
        self.assertIn("post_confirmation_side_effects", task_refs)

        boundary_refs = [
            "inventory_reservation_boundary",
            "payment_validation_boundary",
            "cod_authorization_boundary",
            "order_confirmation_boundary",
            "inventory_commit_boundary",
        ]
        for boundary_ref in boundary_refs:
            boundary = next(task for task in workflow["tasks"] if task["taskReferenceName"] == boundary_ref)
            self.assertEqual(boundary["type"], "SWITCH")
            self.assertIn("FAILED", boundary["decisionCases"])
            failed_refs = [task["taskReferenceName"] for task in boundary["decisionCases"]["FAILED"]]
            self.assertTrue(failed_refs[-1].startswith("terminate_after_"))

        self.assertEqual(
            task_refs[-3:],
            [
                "publish_order_confirmed",
                "post_confirmation_side_effects",
                "join_post_confirmation_side_effects",
            ],
        )
        side_effects = next(task for task in workflow["tasks"] if task["taskReferenceName"] == "post_confirmation_side_effects")
        forked_refs = [
            forked_task["taskReferenceName"]
            for branch in side_effects["forkTasks"]
            for forked_task in branch
        ]
        self.assertEqual(forked_refs, ["generate_invoice", "send_order_notification"])

    def test_conductor_starter_starts_checkout_workflow_idempotently(self) -> None:
        starter = ConductorCheckoutStarter()
        payload = {
            "order_id": "order-1",
            "user_id": "buyer-1",
            "lines": [{"product_id": "aurora-speaker", "quantity": 1}],
            "total": 249,
            "payment_method": "cod",
        }

        first = starter.start_from_checkout_event(
            payload=payload,
            correlation_id="corr-1",
            idempotency_key="checkout-order-1",
        )
        duplicate = starter.start_from_checkout_event(
            payload=payload,
            correlation_id="corr-1",
            idempotency_key="checkout-order-1",
        )

        self.assertEqual(first.workflow_name, "order_checkout_cod")
        self.assertEqual(first.workflow_id, duplicate.workflow_id)
        self.assertEqual(first.input["reservation_id"], "res-order-1")
        self.assertEqual(first.input["payment_id"], "pay-order-1")


if __name__ == "__main__":
    unittest.main()
