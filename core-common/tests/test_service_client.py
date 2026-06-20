import asyncio
import unittest

from core_common.auth import CurrentUser, TokenClaims
from core_common.exceptions import NotFoundError, ServiceCallError
from core_common.http import RequestContext, StaticServiceResolver, StubServiceClient


class ServiceClientTests(unittest.TestCase):
    def test_static_resolver_returns_configured_base_url(self) -> None:
        resolver = StaticServiceResolver({"auth-service": "http://auth:8000/"})

        self.assertEqual(resolver.resolve("auth-service"), "http://auth:8000")

    def test_static_resolver_raises_for_unknown_service(self) -> None:
        resolver = StaticServiceResolver({})

        with self.assertRaises(ServiceCallError) as raised:
            resolver.resolve("missing-service")

        self.assertEqual(raised.exception.service_name, "missing-service")

    def test_stub_service_client_returns_typed_response(self) -> None:
        async def scenario() -> CurrentUser:
            client = StubServiceClient()
            client.add_response(
                "POST",
                "auth-service",
                "/internal/auth/introspect",
                {"sub": "u-1", "email": "u@example.com", "roles": ["customer"]},
            )
            return await client.post(
                "auth-service",
                "/internal/auth/introspect",
                json={"token": "token"},
                response_model=CurrentUser,
                context=RequestContext(correlation_id="cid-1", authorization="Bearer token"),
            )

        user = asyncio.run(scenario())

        self.assertEqual(user.sub, "u-1")
        self.assertEqual(user.email, "u@example.com")
        self.assertEqual(user.roles, ["customer"])

    def test_stub_service_client_records_context_headers(self) -> None:
        async def scenario() -> dict[str, str]:
            client = StubServiceClient()
            client.add_response("GET", "user-service", "/users/u-1", {"id": "u-1"})
            await client.get(
                "user-service",
                "/users/u-1",
                context=RequestContext(correlation_id="cid-1", authorization="Bearer token"),
            )
            return client.calls[0].headers

        headers = asyncio.run(scenario())

        self.assertEqual(headers["X-Correlation-ID"], "cid-1")
        self.assertEqual(headers["Authorization"], "Bearer token")

    def test_stub_service_client_maps_missing_route_to_not_found(self) -> None:
        async def scenario() -> None:
            client = StubServiceClient()
            await client.get("user-service", "/missing")

        with self.assertRaises(NotFoundError):
            asyncio.run(scenario())

    def test_token_claims_to_current_user(self) -> None:
        claims = TokenClaims(sub="u-1", email="u@example.com", roles=["admin"])

        user = claims.to_current_user()

        self.assertEqual(user.sub, "u-1")
        self.assertEqual(user.roles, ["admin"])


if __name__ == "__main__":
    unittest.main()
