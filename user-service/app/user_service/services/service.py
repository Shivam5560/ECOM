from __future__ import annotations

from os import getenv
from typing import Protocol
from uuid import uuid4

import bcrypt
from core_common.auth import CurrentUser
from core_common.exceptions import NotFoundError, ValidationError
from msg_common.bus import EventBus

from user_service.repo.repository import UserProfileRepository
from user_service.schemas import UserProfile


class UserRepo(Protocol):
    def add(self, profile: UserProfile) -> UserProfile: ...
    def list(self) -> list[UserProfile]: ...
    def get(self, profile_id: str) -> UserProfile | None: ...
    def soft_delete(self, profile_id: str) -> UserProfile | None: ...


class UserProfileService:
    def __init__(
        self,
        *,
        event_bus: EventBus,
        database_url: str | None = None,
        repo: UserRepo | None = None,
    ) -> None:
        self.event_bus = event_bus
        if repo is not None:
            self.repo = repo
            return
        database_url = database_url if database_url is not None else getenv("USER_DATABASE_URL")
        if not database_url:
            raise RuntimeError("USER_DATABASE_URL is required for user profile persistence")
        self.repo = UserProfileRepository(database_url)

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
            password_hash=payload.get("password_hash"),
            phone=payload.get("phone"),
        )
        self.repo.add(profile)
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

    async def create_account(
        self,
        *,
        payload: dict,
        correlation_id: str,
    ) -> UserProfile:
        email = str(payload.get("email", "")).strip().lower()
        password = str(payload.get("password", ""))
        display_name = str(payload.get("display_name") or payload.get("full_name") or "").strip()
        if not email or not password or not display_name:
            raise ValidationError("email, password, and display_name are required")
        password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("ascii")
        current_user = CurrentUser(
            sub=str(uuid4()),
            email=email,
            roles=["customer"],
        )
        return await self.create_profile(
            current_user=current_user,
            payload={
                "display_name": display_name,
                "phone": payload.get("phone"),
                "password_hash": password_hash,
            },
            correlation_id=correlation_id,
        )

    async def list_profiles(self) -> list[UserProfile]:
        return self.repo.list()

    async def get_profile(self, profile_id: str) -> UserProfile:
        profile = self.repo.get(profile_id)
        if profile is None:
            raise NotFoundError("user profile not found")
        return profile

    async def soft_delete_profile(self, profile_id: str) -> UserProfile:
        profile = self.repo.soft_delete(profile_id)
        if profile is None:
            raise NotFoundError("user profile not found")
        return profile
