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
    source_service: str
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
        version: str = "1.0",
    ) -> "EventEnvelope":
        return cls(
            event_id=str(uuid4()),
            event_type=event_type,
            correlation_id=correlation_id,
            source_service=source_service,
            timestamp=datetime.now(timezone.utc).isoformat(),
            version=version,
            payload=payload,
        )
