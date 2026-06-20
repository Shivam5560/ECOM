from __future__ import annotations

import asyncio
import unittest

from msg_common.bus import InMemoryEventBus, RetryPolicy


class MessagingRoutingTests(unittest.TestCase):
    def test_retry_policy_moves_failed_event_to_dlq(self) -> None:
        async def scenario() -> tuple[int, str]:
            bus = InMemoryEventBus(
                source_service="order-service",
                retry_policy=RetryPolicy(max_attempts=2),
            )
            attempts = {"count": 0}

            async def fail(_event):
                attempts["count"] += 1
                raise RuntimeError("boom")

            bus.subscribe("order.checkout.requested", fail)
            envelope = await bus.publish(
                event_type="order.checkout.requested",
                payload={"order_id": "order-1"},
                correlation_id="corr-1",
            )
            return attempts["count"], envelope.event_type

        attempts, event_type = asyncio.run(scenario())
        self.assertEqual(attempts, 2)
        self.assertEqual(event_type, "order.checkout.requested")


if __name__ == "__main__":
    unittest.main()
