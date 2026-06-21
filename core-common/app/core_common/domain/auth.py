from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Protocol

from core_common.exceptions import UnauthorizedError


@dataclass(frozen=True, slots=True)
class CurrentUser:
    sub: str
    email: str | None = None
    roles: list[str] = field(default_factory=list)
    exp: int | None = None


@dataclass(frozen=True, slots=True)
class TokenClaims:
    sub: str
    email: str | None = None
    roles: list[str] = field(default_factory=list)
    exp: int | None = None

    def to_current_user(self) -> CurrentUser:
        return CurrentUser(sub=self.sub, email=self.email, roles=list(self.roles), exp=self.exp)


class TokenVerifier(Protocol):
    async def verify(self, token: str) -> CurrentUser:
        ...


class CurrentUserCache(Protocol):
    def get(self, key: str) -> dict[str, Any] | None:
        ...

    def set(self, key: str, value: dict[str, Any], *, ttl_seconds: int) -> None:
        ...


class CurrentUserServiceClient(Protocol):
    async def post(
        self,
        service_name: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        response_model: type[Any] | None = None,
        context: Any | None = None,
    ) -> dict[str, Any]:
        ...


class CurrentUserResolver:
    def __init__(
        self,
        *,
        service_client: CurrentUserServiceClient,
        cache: CurrentUserCache | None = None,
        cache_ttl_seconds: int = 300,
        service_name: str = "user-service",
        resolver_path: str = "/internal/users/current",
    ) -> None:
        self.service_client = service_client
        self.cache = cache
        self.cache_ttl_seconds = cache_ttl_seconds
        self.service_name = service_name
        self.resolver_path = resolver_path

    async def resolve(self, authorization: str | None) -> CurrentUser:
        token = self._extract_bearer_token(authorization)
        cache_key = self._cache_key(token)
        cached = self.cache.get(cache_key) if self.cache is not None else None
        if cached is not None:
            return CurrentUser(
                sub=str(cached["sub"]),
                email=cached.get("email"),
                roles=list(cached.get("roles", [])),
                exp=cached.get("exp"),
            )

        payload = await self.service_client.post(
            self.service_name,
            self.resolver_path,
            json={"token": token},
        )
        if not payload.get("active") or not payload.get("sub"):
            raise UnauthorizedError("invalid auth token")

        current_user = CurrentUser(
            sub=str(payload["sub"]),
            email=payload.get("email"),
            roles=list(payload.get("roles", [])),
            exp=payload.get("exp"),
        )
        if self.cache is not None:
            ttl_seconds = self._ttl_from_payload(payload)
            if ttl_seconds > 0:
                self.cache.set(cache_key, asdict(current_user), ttl_seconds=ttl_seconds)
        return current_user

    def _extract_bearer_token(self, authorization: str | None) -> str:
        if not authorization or not authorization.lower().startswith("bearer "):
            raise UnauthorizedError("authentication is required")
        token = authorization.split(" ", 1)[1].strip()
        if not token:
            raise UnauthorizedError("authentication is required")
        return token

    def _cache_key(self, token: str) -> str:
        digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
        return f"current-user:{digest}"

    def _ttl_from_payload(self, payload: dict[str, Any]) -> int:
        ttl = self.cache_ttl_seconds
        expires_at = payload.get("exp")
        if expires_at is not None:
            ttl = min(ttl, max(0, int(expires_at) - int(time.time())))
        return ttl


class RedisCurrentUserCache:
    def __init__(self, redis_url: str, *, key_prefix: str = "ecom") -> None:
        try:
            from redis import Redis
        except ModuleNotFoundError as exc:
            raise RuntimeError("redis package is required when REDIS_URL is configured") from exc
        self.redis = Redis.from_url(redis_url, decode_responses=True)
        self.key_prefix = key_prefix.rstrip(":")

    def get(self, key: str) -> dict[str, Any] | None:
        raw = self.redis.get(self._key(key))
        if raw is None:
            return None
        return json.loads(raw)

    def set(self, key: str, value: dict[str, Any], *, ttl_seconds: int) -> None:
        self.redis.setex(self._key(key), ttl_seconds, json.dumps(value))

    def _key(self, key: str) -> str:
        return f"{self.key_prefix}:{key}"


_current_user_resolver: CurrentUserResolver | None = None


def get_current_user_resolver() -> CurrentUserResolver:
    global _current_user_resolver
    if _current_user_resolver is not None:
        return _current_user_resolver
    from core_common.http import HttpServiceClient, StaticServiceResolver

    user_service_url = os.getenv("USER_SERVICE_URL")
    if not user_service_url:
        raise RuntimeError("USER_SERVICE_URL is required for current user resolution")
    redis_url = os.getenv("REDIS_URL")
    _current_user_resolver = CurrentUserResolver(
        service_client=HttpServiceClient(StaticServiceResolver({"user-service": user_service_url})),
        cache=RedisCurrentUserCache(redis_url) if redis_url else None,
    )
    return _current_user_resolver


async def get_current_user(authorization: str | None) -> CurrentUser:
    return await get_current_user_resolver().resolve(authorization)


def reset_current_user_resolver() -> None:
    global _current_user_resolver
    _current_user_resolver = None
