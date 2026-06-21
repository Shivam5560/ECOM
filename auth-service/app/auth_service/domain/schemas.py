from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class RegisterRequest:
    email: str
    password: str


@dataclass(frozen=True, slots=True)
class LoginRequest:
    email: str
    password: str


@dataclass(frozen=True, slots=True)
class TokenResponse:
    access_token: str
    token_type: str = "bearer"


@dataclass(frozen=True, slots=True)
class IntrospectionResponse:
    active: bool
    sub: str | None = None
    email: str | None = None
    roles: list[str] = field(default_factory=list)
