from __future__ import annotations

from dataclasses import dataclass
from os import getenv


@dataclass(frozen=True, slots=True)
class AuthSettings:
    issuer: str
    key_id: str
    private_key: str
    public_key: str
    database_url: str

    @classmethod
    def from_env(cls) -> "AuthSettings":
        return cls(
            issuer=getenv("AUTH_ISSUER", "auth-service"),
            key_id=getenv("AUTH_KEY_ID", "local-dev"),
            private_key=getenv("AUTH_PRIVATE_KEY", "dev-private-key"),
            public_key=getenv("AUTH_PUBLIC_KEY", "dev-public-key"),
            database_url=getenv(
                "AUTH_DATABASE_URL",
                "postgresql+asyncpg://ecom:ecom@localhost:5432/auth_db",
            ),
        )
