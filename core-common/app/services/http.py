from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, TypeVar

from core_common.exceptions import NotFoundError, ServiceCallError

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class RequestContext:
    correlation_id: str | None = None
    authorization: str | None = None

    def to_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        if self.correlation_id:
            headers["X-Correlation-ID"] = self.correlation_id
        if self.authorization:
            headers["Authorization"] = self.authorization
        return headers


class ServiceResolver(Protocol):
    def resolve(self, service_name: str) -> str:
        ...


class StaticServiceResolver:
    def __init__(self, services: dict[str, str]) -> None:
        self._services = services

    def resolve(self, service_name: str) -> str:
        try:
            return self._services[service_name].rstrip("/")
        except KeyError as exc:
            raise ServiceCallError(service_name, "service is not configured") from exc


class ServiceClient(Protocol):
    async def get(
        self,
        service_name: str,
        path: str,
        *,
        response_model: type[T] | None = None,
        context: RequestContext | None = None,
    ) -> T | dict[str, Any]:
        ...

    async def post(
        self,
        service_name: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        response_model: type[T] | None = None,
        context: RequestContext | None = None,
    ) -> T | dict[str, Any]:
        ...


@dataclass(frozen=True, slots=True)
class RecordedCall:
    method: str
    service_name: str
    path: str
    body: dict[str, Any] | None
    headers: dict[str, str] = field(default_factory=dict)


class StubServiceClient:
    def __init__(self) -> None:
        self._responses: dict[tuple[str, str, str], dict[str, Any]] = {}
        self.calls: list[RecordedCall] = []

    def add_response(
        self,
        method: str,
        service_name: str,
        path: str,
        payload: dict[str, Any],
    ) -> None:
        self._responses[(method.upper(), service_name, path)] = payload

    async def get(
        self,
        service_name: str,
        path: str,
        *,
        response_model: type[T] | None = None,
        context: RequestContext | None = None,
    ) -> T | dict[str, Any]:
        return await self._request(
            "GET",
            service_name,
            path,
            body=None,
            response_model=response_model,
            context=context,
        )

    async def post(
        self,
        service_name: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        response_model: type[T] | None = None,
        context: RequestContext | None = None,
    ) -> T | dict[str, Any]:
        return await self._request(
            "POST",
            service_name,
            path,
            body=json,
            response_model=response_model,
            context=context,
        )

    async def _request(
        self,
        method: str,
        service_name: str,
        path: str,
        *,
        body: dict[str, Any] | None,
        response_model: type[T] | None,
        context: RequestContext | None,
    ) -> T | dict[str, Any]:
        headers = context.to_headers() if context else {}
        self.calls.append(
            RecordedCall(
                method=method,
                service_name=service_name,
                path=path,
                body=body,
                headers=headers,
            )
        )
        key = (method, service_name, path)
        if key not in self._responses:
            raise NotFoundError(f"no stub response for {method} {service_name}{path}")
        payload = self._responses[key]
        if response_model is None:
            return payload
        return response_model(**payload)
