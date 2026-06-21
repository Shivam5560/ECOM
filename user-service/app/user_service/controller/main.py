from __future__ import annotations
import dataclasses
from os import getenv
from fastapi.middleware.cors import CORSMiddleware

from core_common.auth import CurrentUser, CurrentUserResolver, RedisCurrentUserCache
from core_common.http import HttpServiceClient, StaticServiceResolver
from msg_common.bus import InMemoryEventBus
from user_service.services.service import UserProfileService
from core_common.exceptions import AppError


def _auth_current_user_resolver() -> CurrentUserResolver:
    auth_service_url = getenv("AUTH_SERVICE_URL")
    if not auth_service_url:
        raise RuntimeError("AUTH_SERVICE_URL is required for current user resolution")
    redis_url = getenv("REDIS_URL")
    return CurrentUserResolver(
        service_client=HttpServiceClient(StaticServiceResolver({"auth-service": auth_service_url})),
        cache=RedisCurrentUserCache(redis_url) if redis_url else None,
        service_name="auth-service",
        resolver_path="/internal/auth/introspect",
    )


def create_app():
    from fastapi import FastAPI, Header, HTTPException

    app = FastAPI(title="user-service")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    service = UserProfileService(
        event_bus=InMemoryEventBus(source_service="user-service")
    )
    current_user_resolver = _auth_current_user_resolver()

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/ready")
    async def ready() -> dict[str, str]:
        return {"status": "ready"}

    @app.post("/internal/users/current")
    async def current_user(payload: dict) -> dict:
        user = await current_user_resolver.resolve(f"Bearer {payload.get('token', '')}")
        return {"active": True, "sub": user.sub, "email": user.email, "roles": user.roles, "exp": user.exp}

    @app.post("/api/v1/users")
    async def create_user(payload: dict, authorization: str | None = Header(None)) -> dict:
        try:
            if payload.get("password"):
                profile = await service.create_account(
                    payload=payload,
                    correlation_id=payload.get("correlation_id", "missing"),
                )
            else:
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
            return dataclasses.asdict(profile)
        except AppError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    @app.get("/api/v1/users")
    async def list_users() -> list[dict]:
        return [dataclasses.asdict(profile) for profile in await service.list_profiles()]

    @app.get("/api/v1/users/{user_id}")
    async def get_user(user_id: str) -> dict:
        return dataclasses.asdict(await service.get_profile(user_id))

    @app.delete("/api/v1/users/{user_id}")
    async def delete_user(user_id: str) -> dict:
        return dataclasses.asdict(await service.soft_delete_profile(user_id))

    return app
