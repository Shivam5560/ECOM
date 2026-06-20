from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True, slots=True)
class CurrentUser:
    sub: str
    email: str | None = None
    roles: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class TokenClaims:
    sub: str
    email: str | None = None
    roles: list[str] = field(default_factory=list)

    def to_current_user(self) -> CurrentUser:
        return CurrentUser(sub=self.sub, email=self.email, roles=list(self.roles))


class TokenVerifier(Protocol):
    async def verify(self, token: str) -> CurrentUser:
        ...
