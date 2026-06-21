import asyncio
import unittest
from os import getenv

from core_common.auth import CurrentUser
from msg_common.bus import InMemoryEventBus
from user_service.repo.repository import UserProfileRepository
from user_service.service import UserProfileService


class FakeUserProfileRepository:
    def __init__(self) -> None:
        self.profiles = {}

    def add(self, profile):
        self.profiles[profile.id] = profile
        return profile

    def list(self):
        return [profile for profile in self.profiles.values() if profile.deleted_at is None]

    def get(self, profile_id):
        profile = self.profiles.get(profile_id)
        return profile if profile and profile.deleted_at is None else None

    def soft_delete(self, profile_id):
        profile = self.get(profile_id)
        if profile:
            from datetime import datetime, timezone
            profile.deleted_at = datetime.now(timezone.utc)
            profile.is_active = False
        return profile


def service_with_repo(bus=None):
    return UserProfileService(
        event_bus=bus or InMemoryEventBus(source_service="user-service"),
        repo=FakeUserProfileRepository(),
    )


class UserProfileServiceTests(unittest.TestCase):
    def test_create_profile_uses_token_subject_as_owner(self) -> None:
        async def scenario():
            bus = InMemoryEventBus(source_service="user-service")
            service = service_with_repo(bus)
            current_user = CurrentUser(
                sub="auth-1",
                email="owner@example.com",
                roles=["customer"],
            )
            profile = await service.create_profile(
                current_user=current_user,
                payload={"display_name": "Owner", "phone": "+100000000"},
                correlation_id="cid-1",
            )
            return profile, bus.published

        profile, events = asyncio.run(scenario())

        self.assertEqual(profile.auth_subject, "auth-1")
        self.assertEqual(profile.email, "owner@example.com")
        self.assertEqual(profile.display_name, "Owner")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].event_type, "user.registered")
        self.assertEqual(events[0].payload["auth_subject"], "auth-1")

    def test_create_account_stores_bcrypt_password_hash(self) -> None:
        async def scenario():
            service = service_with_repo()
            return await service.create_account(
                payload={
                    "email": "new@example.com",
                    "password": "secret-password",
                    "display_name": "New Buyer",
                },
                correlation_id="cid-1",
            )

        profile = asyncio.run(scenario())

        self.assertEqual(profile.email, "new@example.com")
        self.assertEqual(profile.display_name, "New Buyer")
        self.assertIsNotNone(profile.password_hash)
        self.assertNotEqual(profile.password_hash, "secret-password")
        self.assertTrue(profile.password_hash.startswith(("$2a$", "$2b$", "$2y$")))

    def test_soft_delete_marks_profile_deleted(self) -> None:
        async def scenario():
            service = service_with_repo()
            profile = await service.create_profile(
                current_user=CurrentUser(sub="auth-1", email="owner@example.com"),
                payload={"display_name": "Owner"},
                correlation_id="cid-1",
            )
            deleted = await service.soft_delete_profile(profile.id)
            return deleted

        deleted = asyncio.run(scenario())

        self.assertIsNotNone(deleted.deleted_at)
        self.assertFalse(deleted.is_active)

    def test_list_profiles_excludes_deleted_profiles(self) -> None:
        async def scenario():
            service = service_with_repo()
            first = await service.create_profile(
                current_user=CurrentUser(sub="auth-1", email="one@example.com"),
                payload={"display_name": "One"},
                correlation_id="cid-1",
            )
            await service.create_profile(
                current_user=CurrentUser(sub="auth-2", email="two@example.com"),
                payload={"display_name": "Two"},
                correlation_id="cid-2",
            )
            await service.soft_delete_profile(first.id)
            return await service.list_profiles()

        profiles = asyncio.run(scenario())

        self.assertEqual(len(profiles), 1)
        self.assertEqual(profiles[0].auth_subject, "auth-2")

    @unittest.skipUnless(getenv("USER_TEST_DATABASE_URL"), "USER_TEST_DATABASE_URL is not configured")
    def test_repository_uses_user_test_database(self) -> None:
        async def scenario():
            service = UserProfileService(
                event_bus=InMemoryEventBus(source_service="user-service"),
                repo=UserProfileRepository(getenv("USER_TEST_DATABASE_URL", "")),
            )
            return await service.create_profile(
                current_user=CurrentUser(sub="auth-test", email="test@example.com"),
                payload={"display_name": "Test User"},
                correlation_id="cid-1",
            )

        profile = asyncio.run(scenario())

        self.assertEqual(profile.auth_subject, "auth-test")


if __name__ == "__main__":
    unittest.main()
