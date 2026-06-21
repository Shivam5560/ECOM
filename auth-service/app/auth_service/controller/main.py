from __future__ import annotations
import dataclasses
from fastapi.middleware.cors import CORSMiddleware

from auth_service.config import AuthSettings
from auth_service.repo.repository import AuthUserRepository
from auth_service.security import PasswordHasher, TokenIssuer
from core_common.exceptions import AppError, UnauthorizedError, ValidationError


def create_token_issuer(settings: AuthSettings | None = None) -> TokenIssuer:
    settings = settings or AuthSettings.from_env()
    return TokenIssuer(
        issuer=settings.issuer,
        key_id=settings.key_id,
        private_key=settings.private_key,
        public_key=settings.public_key,
    )


def create_app():
    from fastapi import FastAPI

    app = FastAPI(title="auth-service")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    issuer = create_token_issuer()
    hasher = PasswordHasher()
    repo = AuthUserRepository(AuthSettings.from_env().database_url)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/ready")
    async def ready() -> dict[str, str]:
        return {"status": "ready"}

    @app.get("/.well-known/jwks.json")
    async def jwks() -> dict:
        return issuer.jwks()

    @app.post("/internal/auth/introspect")
    async def introspect(payload: dict) -> dict:
        try:
            claims = issuer.verify_token(payload["token"])
        except Exception:
            return {"active": False}
        return {
            "active": True,
            "sub": claims.sub,
            "email": claims.email,
            "roles": claims.roles,
            "exp": claims.exp,
        }

    @app.post("/api/v1/auth/login")
    async def login(payload: dict) -> dict:
        from fastapi import HTTPException

        try:
            email = str(payload.get("email", "")).strip().lower()
            password = str(payload.get("password", ""))
            user = repo.find_by_email(email)
            if user is None or not hasher.verify_password(password, user.password_hash):
                raise UnauthorizedError("invalid email or password")
            token = issuer.issue_access_token(subject=user.id, email=user.email, roles=list(user.roles))
            return {"access_token": token, "token_type": "bearer"}
        except AppError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    @app.post("/oauth/token")
    async def oauth_token(payload: dict) -> dict:
        return await login({"email": payload.get("username", ""), "password": payload.get("password", "")})

    @app.post("/api/v1/auth/register")
    async def register(payload: dict) -> dict:
        from fastapi import HTTPException

        try:
            email = str(payload.get("email", "")).strip().lower()
            password = str(payload.get("password", ""))
            if not email or not password:
                raise ValidationError("email and password are required")
            existing = repo.find_by_email(email)
            user = existing or repo.create_user(email=email, password_hash=hasher.hash_password(password))
            token = issuer.issue_access_token(subject=user.id, email=user.email, roles=list(user.roles))
            return {"access_token": token, "token_type": "bearer"}
        except AppError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    return app
