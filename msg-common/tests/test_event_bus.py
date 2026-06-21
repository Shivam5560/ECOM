import asyncio
import unittest

from msg_common.bus import DomainRouting, InMemoryEventBus
from msg_common.envelope import EventEnvelope


class EventBusTests(unittest.TestCase):
    def test_event_envelope_sets_required_metadata(self) -> None:
        envelope = EventEnvelope.create(
            event_type="user.registered",
            source_service="user-service",
            payload={"user_id": "u-1"},
            correlation_id="cid-1",
            idempotency_key="user-u-1",
        )

        self.assertEqual(envelope.event_type, "user.registered")
        self.assertEqual(envelope.source_service, "user-service")
        self.assertEqual(envelope.payload, {"user_id": "u-1"})
        self.assertEqual(envelope.correlation_id, "cid-1")
        self.assertEqual(envelope.idempotency_key, "user-u-1")
        self.assertTrue(envelope.occurred_at)
        self.assertEqual(envelope.version, "1.0")
        self.assertTrue(envelope.event_id)
        self.assertTrue(envelope.timestamp)

    def test_domain_routing_names_checkout_exchange_and_routes(self) -> None:
        self.assertEqual(DomainRouting.exchange, "ecom.domain")
        self.assertEqual(DomainRouting.order_checkout_requested, "order.checkout.requested")
        self.assertEqual(DomainRouting.order_confirmed, "order.confirmed")
        self.assertEqual(DomainRouting.invoice_generate_requested, "invoice.generate.requested")
        self.assertEqual(DomainRouting.notification_send_requested, "notification.send.requested")

    def test_in_memory_event_bus_delivers_to_subscriber(self) -> None:
        async def scenario() -> list[EventEnvelope]:
            bus = InMemoryEventBus(source_service="user-service")
            seen: list[EventEnvelope] = []

            async def handler(event: EventEnvelope) -> None:
                seen.append(event)

            bus.subscribe("user.registered", handler)
            await bus.publish(
                event_type="user.registered",
                payload={"user_id": "u-1"},
                correlation_id="cid-1",
                idempotency_key="user-u-1",
            )
            return seen

        seen = asyncio.run(scenario())

        self.assertEqual(len(seen), 1)
        self.assertEqual(seen[0].event_type, "user.registered")
        self.assertEqual(seen[0].payload, {"user_id": "u-1"})
        self.assertEqual(seen[0].idempotency_key, "user-u-1")


if __name__ == "__main__":
    unittest.main()
