from __future__ import annotations

from collections import defaultdict
from typing import Any, Protocol


class RealtimeConnection(Protocol):
    async def send_json(self, payload: dict[str, Any]) -> None:
        ...


class RealtimeHub:
    def __init__(self) -> None:
        self._connections: dict[str, list[RealtimeConnection]] = defaultdict(list)

    def connect(self, channel: str, connection: RealtimeConnection) -> None:
        self._connections[channel].append(connection)

    def disconnect(self, channel: str, connection: RealtimeConnection) -> None:
        if connection in self._connections[channel]:
            self._connections[channel].remove(connection)

    async def publish(self, channel: str, payload: dict[str, Any]) -> None:
        for connection in list(self._connections[channel]):
            await connection.send_json(payload)
