from __future__ import annotations

from dataclasses import dataclass, field
from math import ceil
from typing import Any, Generic, TypeVar

from core_common.exceptions import AppError

T = TypeVar("T")


@dataclass(slots=True)
class ResponseEnvelope(Generic[T]):
    data: T | None = None
    message: str | None = None
    meta: dict[str, Any] = field(default_factory=dict)
    success: bool = True


@dataclass(slots=True)
class ErrorEnvelope:
    error: dict[str, Any]
    success: bool = False

    @classmethod
    def from_exception(
        cls,
        error: Exception,
        *,
        correlation_id: str | None = None,
    ) -> "ErrorEnvelope":
        code = getattr(error, "code", "internal_error")
        message = getattr(error, "message", str(error))
        payload: dict[str, Any] = {"code": code, "message": message}
        if correlation_id:
            payload["correlation_id"] = correlation_id
        if isinstance(error, AppError):
            payload["status_code"] = error.status_code
        return cls(error=payload)


@dataclass(slots=True)
class GridParams:
    page: int = 1
    size: int = 20
    sort_by: str | None = None
    order: str = "asc"
    filters: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.page = max(1, self.page)
        self.size = min(100, max(1, self.size))
        order = self.order.lower()
        self.order = order if order in {"asc", "desc"} else "asc"

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size


@dataclass(slots=True)
class PagedResponse(Generic[T]):
    items: list[T]
    total: int
    page: int
    size: int

    @property
    def pages(self) -> int:
        if self.total <= 0:
            return 0
        return ceil(self.total / self.size)
