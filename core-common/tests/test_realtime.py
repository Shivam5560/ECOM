from __future__ import annotations

import asyncio
import unittest

from core_common.realtime import RealtimeHub


class FakeConnection:
    def __init__(self) -> None:
        self.messages: list[dict] = []

    async def send_json(self, payload: dict) -> None:
        self.messages.append(payload)


class RealtimeHubTests(unittest.TestCase):
    def test_publish_sends_message_to_channel_connections(self) -> None:
        async def scenario() -> list[dict]:
            hub = RealtimeHub()
            connection = FakeConnection()
            hub.connect("buyer-1", connection)
            await hub.publish("buyer-1", {"type": "order.confirmed"})
            return connection.messages

        self.assertEqual(asyncio.run(scenario()), [{"type": "order.confirmed"}])


if __name__ == "__main__":
    unittest.main()
