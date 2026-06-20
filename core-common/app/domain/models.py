from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from math import ceil
from typing import Any, Generic, TypeVar
from uuid import uuid4

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


@dataclass(frozen=True, slots=True)
class GridColumn:
    key: str
    label: str
    sortable: bool = True
    filterable: bool = False
    kind: str = "text"


@dataclass(slots=True)
class PagedResponse(Generic[T]):
    items: list[T]
    total: int
    page: int
    size: int
    columns: list[GridColumn] = field(default_factory=list)
    actions: list[dict[str, Any]] = field(
        default_factory=lambda: [
            {"key": "view", "label": "View"},
            {"key": "edit", "label": "Edit"},
            {"key": "delete", "label": "Delete"},
        ]
    )

    @property
    def pages(self) -> int:
        if self.total <= 0:
            return 0
        return ceil(self.total / self.size)


@dataclass(slots=True)
class AuditEntity:
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: datetime | None = None
    created_by: str | None = None
    updated_by: str | None = None
    deleted_by: str | None = None
    is_active: bool = True

    def touch(self, user_id: str | None = None) -> None:
        self.updated_at = datetime.now(timezone.utc)
        self.updated_by = user_id

    def soft_delete(self, user_id: str | None = None) -> None:
        self.deleted_at = datetime.now(timezone.utc)
        self.deleted_by = user_id
        self.is_active = False
        self.touch(user_id)


class InMemoryRepository(Generic[T]):
    def __init__(self) -> None:
        self._items: dict[str, T] = {}

    def add(self, item: T) -> T:
        self._items[getattr(item, "id")] = item
        return item

    def get(self, item_id: str) -> T | None:
        item = self._items.get(item_id)
        if item is None or getattr(item, "deleted_at", None) is not None:
            return None
        return item

    def soft_delete(self, item_id: str, *, deleted_by: str | None = None) -> T | None:
        item = self._items.get(item_id)
        if item is None:
            return None
        soft_delete = getattr(item, "soft_delete")
        soft_delete(deleted_by)
        return item

    def list(
        self,
        params: GridParams | None = None,
        *,
        columns: list[GridColumn] | None = None,
        actions: list[dict[str, Any]] | None = None,
    ) -> PagedResponse[T]:
        params = params or GridParams()
        items = [
            item
            for item in self._items.values()
            if getattr(item, "deleted_at", None) is None
        ]
        filtered = self._apply_filters(items, params)
        sorted_items = self._apply_sort(filtered, params)
        paged = sorted_items[params.offset : params.offset + params.size]
        return PagedResponse(
            items=paged,
            total=len(sorted_items),
            page=params.page,
            size=params.size,
            columns=columns or [],
            actions=actions
            or [
                {"key": "view", "label": "View"},
                {"key": "edit", "label": "Edit"},
                {"key": "delete", "label": "Delete"},
            ],
        )

    def _apply_filters(self, items: list[T], params: GridParams) -> list[T]:
        filtered = items
        for key, expected in params.filters.items():
            filtered = [
                item
                for item in filtered
                if str(getattr(item, key, "")).lower() == str(expected).lower()
            ]
        return filtered

    def _apply_sort(self, items: list[T], params: GridParams) -> list[T]:
        if not params.sort_by:
            return items
        reverse = params.order == "desc"
        return sorted(items, key=lambda item: getattr(item, params.sort_by or "", ""), reverse=reverse)
