from __future__ import annotations

from auth_service.config import AuthSettings
from auth_service.security import PasswordHasher, TokenIssuer


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
    issuer = create_token_issuer()
    hasher = PasswordHasher()

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
        }

    @app.post("/auth/login")
    async def login(payload: dict) -> dict:
        token = issuer.issue_access_token(
            subject=payload.get("email", "unknown"),
            email=payload.get("email", "unknown"),
            roles=["customer"],
        )
        return {"access_token": token, "token_type": "bearer"}

    @app.post("/oauth/token")
    async def oauth_token(payload: dict) -> dict:
        token = issuer.issue_access_token(
            subject=payload.get("username", "unknown"),
            email=payload.get("username", "unknown"),
            roles=["customer"],
        )
        return {"access_token": token, "token_type": "bearer"}

    @app.post("/auth/register")
    async def register(payload: dict) -> dict:
        token = issuer.issue_access_token(
            subject=payload.get("email", "unknown"),
            email=payload.get("email", "unknown"),
            roles=["customer"],
        )
        return {
            "subject": payload.get("email", "unknown"),
            "password_hash": hasher.hash_password(payload.get("password", "")),
            "access_token": token,
            "token_type": "bearer",
        }

    return app
