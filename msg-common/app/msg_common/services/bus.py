from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Awaitable, Callable, ClassVar, Protocol

from msg_common.envelope import EventEnvelope

EventHandler = Callable[[EventEnvelope], Awaitable[None]]


class DomainRouting:
    exchange: ClassVar[str] = "ecom.domain"
    order_checkout_requested: ClassVar[str] = "order.checkout.requested"
    order_confirmed: ClassVar[str] = "order.confirmed"
    order_checkout_failed: ClassVar[str] = "order.checkout.failed"
    invoice_generate_requested: ClassVar[str] = "invoice.generate.requested"
    invoice_generated: ClassVar[str] = "invoice.generated"
    notification_send_requested: ClassVar[str] = "notification.send.requested"
    notification_created: ClassVar[str] = "notification.created"


class EventBus(Protocol):
    async def publish(
        self,
        *,
        event_type: str,
        payload: dict,
        correlation_id: str,
        idempotency_key: str | None = None,
    ) -> EventEnvelope:
        ...

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        ...


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    max_attempts: int = 3
    dlq_suffix: str = ".dlq"


class InMemoryEventBus:
    def __init__(self, *, source_service: str, retry_policy: RetryPolicy | None = None) -> None:
        self.source_service = source_service
        self.retry_policy = retry_policy or RetryPolicy()
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)
        self.published: list[EventEnvelope] = []
        self.dead_letters: list[EventEnvelope] = []

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        self._handlers[event_type].append(handler)

    async def publish(
        self,
        *,
        event_type: str,
        payload: dict,
        correlation_id: str,
        idempotency_key: str | None = None,
    ) -> EventEnvelope:
        envelope = EventEnvelope.create(
            event_type=event_type,
            source_service=self.source_service,
            payload=payload,
            correlation_id=correlation_id,
            idempotency_key=idempotency_key,
        )
        self.published.append(envelope)
        for handler in self._handlers[event_type]:
            for attempt in range(self.retry_policy.max_attempts):
                try:
                    await handler(envelope)
                    break
                except Exception:
                    if attempt + 1 >= self.retry_policy.max_attempts:
                        self.dead_letters.append(envelope)
        return envelope
