from __future__ import annotations

from core_common.auth import CurrentUser
from msg_common.bus import InMemoryEventBus
from services.service import UserProfileService


def create_app():
    from fastapi import FastAPI, Header, HTTPException

    app = FastAPI(title="user-service")
    service = UserProfileService(
        event_bus=InMemoryEventBus(source_service="user-service")
    )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/ready")
    async def ready() -> dict[str, str]:
        return {"status": "ready"}

    @app.post("/users")
    async def create_user(payload: dict, authorization: str | None = Header(None)) -> dict:
        if not authorization:
            raise HTTPException(status_code=401, detail="missing bearer token")
        current_user = CurrentUser(
            sub=payload.get("auth_subject", "unknown"),
            email=payload.get("email"),
            roles=["customer"],
        )
        profile = await service.create_profile(
            current_user=current_user,
            payload=payload,
            correlation_id=payload.get("correlation_id", "missing"),
        )
        return profile.__dict__

    @app.get("/users")
    async def list_users() -> list[dict]:
        return [profile.__dict__ for profile in await service.list_profiles()]

    @app.get("/users/{user_id}")
    async def get_user(user_id: str) -> dict:
        return (await service.get_profile(user_id)).__dict__

    @app.delete("/users/{user_id}")
    async def delete_user(user_id: str) -> dict:
        return (await service.soft_delete_profile(user_id)).__dict__

    return app
