from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from functools import wraps
from typing import Any, ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")


@dataclass(slots=True)
class CacheEntry:
    value: Any
    expires_at: float


class InMemoryCacheBackend:
    def __init__(self) -> None:
        self._items: dict[str, CacheEntry] = {}

    def get(self, key: str) -> Any | None:
        entry = self._items.get(key)
        if entry is None:
            return None
        if entry.expires_at < time.time():
            self._items.pop(key, None)
            return None
        return entry.value

    def set(self, key: str, value: Any, *, ttl_seconds: int) -> None:
        self._items[key] = CacheEntry(value=value, expires_at=time.time() + ttl_seconds)

    def invalidate_prefix(self, prefix: str) -> None:
        for key in list(self._items):
            if key.startswith(prefix):
                self._items.pop(key, None)


def cacheable(
    *,
    backend: InMemoryCacheBackend,
    ttl_seconds: int,
    key_prefix: str,
) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
    def decorator(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            key = f"{key_prefix}:{args!r}:{sorted(kwargs.items())!r}"
            cached = backend.get(key)
            if cached is not None:
                return cached
            value = await func(*args, **kwargs)
            backend.set(key, value, ttl_seconds=ttl_seconds)
            return value

        return wrapper

    return decorator
