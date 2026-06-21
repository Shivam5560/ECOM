from __future__ import annotations

import asyncio
import unittest
from unittest.mock import patch

from core_common.auth import CurrentUserResolver, get_current_user_resolver, reset_current_user_resolver
from core_common.cache import InMemoryCacheBackend
from core_common.exceptions import UnauthorizedError
from core_common.http import StubServiceClient


class CurrentUserResolverTests(unittest.TestCase):
    def tearDown(self) -> None:
        reset_current_user_resolver()

    def test_resolver_introspects_token_and_caches_current_user_by_token_hash(self) -> None:
        async def scenario():
            client = StubServiceClient()
            client.add_response(
                "POST",
                "user-service",
                "/internal/users/current",
                {
                    "active": True,
                    "sub": "user-1",
                    "email": "user@example.com",
                    "roles": ["customer"],
                    "exp": 9_999_999_999,
                },
            )
            cache = InMemoryCacheBackend()
            resolver = CurrentUserResolver(service_client=client, cache=cache)

            first = await resolver.resolve("Bearer token-1")
            second = await resolver.resolve("Bearer token-1")

            return first, second, client.calls, cache._items

        first, second, calls, cache_items = asyncio.run(scenario())

        self.assertEqual(first.sub, "user-1")
        self.assertEqual(second.email, "user@example.com")
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0].service_name, "user-service")
        self.assertEqual(calls[0].path, "/internal/users/current")
        self.assertEqual(calls[0].body, {"token": "token-1"})
        self.assertNotIn("token-1", next(iter(cache_items)))

    def test_resolver_rejects_missing_or_inactive_token(self) -> None:
        async def scenario():
            client = StubServiceClient()
            client.add_response(
                "POST",
                "user-service",
                "/internal/users/current",
                {"active": False},
            )
            resolver = CurrentUserResolver(service_client=client)
            with self.assertRaises(UnauthorizedError):
                await resolver.resolve(None)
            with self.assertRaises(UnauthorizedError):
                await resolver.resolve("Bearer bad-token")

        asyncio.run(scenario())

    def test_get_current_user_resolver_builds_singleton_from_environment(self) -> None:
        with patch.dict(
            "os.environ",
            {
                "USER_SERVICE_URL": "http://user-service:8000",
                "REDIS_URL": "",
            },
            clear=False,
        ), patch("core_common.http.httpx", object()):
            first = get_current_user_resolver()
            second = get_current_user_resolver()

        self.assertIs(first, second)
        self.assertIsInstance(first, CurrentUserResolver)


if __name__ == "__main__":
    unittest.main()
