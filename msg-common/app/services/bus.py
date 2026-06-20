from __future__ import annotations

from collections import defaultdict
from typing import Awaitable, Callable, Protocol

from msg_common.envelope import EventEnvelope

EventHandler = Callable[[EventEnvelope], Awaitable[None]]


class EventBus(Protocol):
    async def publish(
        self,
        *,
        event_type: str,
        payload: dict,
        correlation_id: str,
    ) -> EventEnvelope:
        ...

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        ...


class InMemoryEventBus:
    def __init__(self, *, source_service: str) -> None:
        self.source_service = source_service
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)
        self.published: list[EventEnvelope] = []

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        self._handlers[event_type].append(handler)

    async def publish(
        self,
        *,
        event_type: str,
        payload: dict,
        correlation_id: str,
    ) -> EventEnvelope:
        envelope = EventEnvelope.create(
            event_type=event_type,
            source_service=self.source_service,
            payload=payload,
            correlation_id=correlation_id,
        )
        self.published.append(envelope)
        for handler in self._handlers[event_type]:
            await handler(envelope)
        return envelope
