from __future__ import annotations

from core_common.auth import CurrentUser
from core_common.http import RequestContext, ServiceClient


class AuthClient:
    def __init__(self, service_client: ServiceClient) -> None:
        self.service_client = service_client

    async def introspect_token(
        self,
        token: str,
        *,
        correlation_id: str | None = None,
    ) -> CurrentUser | None:
        response = await self.service_client.post(
            "auth-service",
            "/internal/auth/introspect",
            json={"token": token},
            context=RequestContext(
                correlation_id=correlation_id,
                authorization=f"Bearer {token}",
            ),
        )
        if not response.get("active"):
            return None
        return CurrentUser(
            sub=response["sub"],
            email=response.get("email"),
            roles=list(response.get("roles", [])),
        )
