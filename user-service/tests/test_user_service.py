import asyncio
import unittest

from core_common.auth import CurrentUser
from msg_common.bus import InMemoryEventBus
from user_service.service import UserProfileService


class UserProfileServiceTests(unittest.TestCase):
    def test_create_profile_uses_token_subject_as_owner(self) -> None:
        async def scenario():
            bus = InMemoryEventBus(source_service="user-service")
            service = UserProfileService(event_bus=bus)
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

    def test_soft_delete_marks_profile_deleted(self) -> None:
        async def scenario():
            service = UserProfileService(
                event_bus=InMemoryEventBus(source_service="user-service")
            )
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
            service = UserProfileService(
                event_bus=InMemoryEventBus(source_service="user-service")
            )
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


if __name__ == "__main__":
    unittest.main()
