import asyncio
import unittest

from msg_common.bus import InMemoryEventBus
from msg_common.envelope import EventEnvelope


class EventBusTests(unittest.TestCase):
    def test_event_envelope_sets_required_metadata(self) -> None:
        envelope = EventEnvelope.create(
            event_type="user.registered",
            source_service="user-service",
            payload={"user_id": "u-1"},
            correlation_id="cid-1",
        )

        self.assertEqual(envelope.event_type, "user.registered")
        self.assertEqual(envelope.source_service, "user-service")
        self.assertEqual(envelope.payload, {"user_id": "u-1"})
        self.assertEqual(envelope.correlation_id, "cid-1")
        self.assertEqual(envelope.version, "1.0")
        self.assertTrue(envelope.event_id)
        self.assertTrue(envelope.timestamp)

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
            )
            return seen

        seen = asyncio.run(scenario())

        self.assertEqual(len(seen), 1)
        self.assertEqual(seen[0].event_type, "user.registered")
        self.assertEqual(seen[0].payload, {"user_id": "u-1"})


if __name__ == "__main__":
    unittest.main()
