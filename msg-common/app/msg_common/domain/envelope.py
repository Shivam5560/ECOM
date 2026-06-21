from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class EventEnvelope:
    event_id: str
    event_type: str
    correlation_id: str
    idempotency_key: str
    source_service: str
    occurred_at: str
    timestamp: str
    version: str
    payload: dict[str, Any]

    @classmethod
    def create(
        cls,
        *,
        event_type: str,
        source_service: str,
        payload: dict[str, Any],
        correlation_id: str,
        idempotency_key: str | None = None,
        version: str = "1.0",
    ) -> "EventEnvelope":
        occurred_at = datetime.now(timezone.utc).isoformat()
        return cls(
            event_id=str(uuid4()),
            event_type=event_type,
            correlation_id=correlation_id,
            idempotency_key=idempotency_key or correlation_id,
            source_service=source_service,
            occurred_at=occurred_at,
            timestamp=occurred_at,
            version=version,
            payload=payload,
        )
