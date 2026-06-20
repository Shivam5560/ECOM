from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from core_common.auth import CurrentUser
from core_common.exceptions import NotFoundError
from msg_common.bus import EventBus

from user_service.schemas import UserProfile


class UserProfileService:
    def __init__(self, *, event_bus: EventBus) -> None:
        self.event_bus = event_bus
        self._profiles: dict[str, UserProfile] = {}

    async def create_profile(
        self,
        *,
        current_user: CurrentUser,
        payload: dict,
        correlation_id: str,
    ) -> UserProfile:
        profile = UserProfile(
            id=str(uuid4()),
            auth_subject=current_user.sub,
            email=current_user.email,
            display_name=payload["display_name"],
            phone=payload.get("phone"),
        )
        self._profiles[profile.id] = profile
        await self.event_bus.publish(
            event_type="user.registered",
            payload={
                "user_id": profile.id,
                "auth_subject": profile.auth_subject,
                "email": profile.email,
            },
            correlation_id=correlation_id,
        )
        return profile

    async def list_profiles(self) -> list[UserProfile]:
        return [
            profile
            for profile in self._profiles.values()
            if profile.deleted_at is None
        ]

    async def get_profile(self, profile_id: str) -> UserProfile:
        profile = self._profiles.get(profile_id)
        if profile is None or profile.deleted_at is not None:
            raise NotFoundError("user profile not found")
        return profile

    async def soft_delete_profile(self, profile_id: str) -> UserProfile:
        profile = await self.get_profile(profile_id)
        profile.deleted_at = datetime.now(timezone.utc)
        profile.is_active = False
        return profile
