from __future__ import annotations

from datetime import datetime
from uuid import uuid4

try:
    from sqlalchemy import DateTime, JSON, String, create_engine, func
    from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column
    from sqlalchemy.engine import Engine
except ModuleNotFoundError:
    create_engine = None
    Engine = object  # type: ignore[misc,assignment]


class Base(DeclarativeBase):
    pass


class AuthUserRow(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    roles: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=lambda: ["customer"])
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)


class AuthUserRepository:
    def __init__(self, database_url: str) -> None:
        if create_engine is None:
            raise RuntimeError("sqlalchemy is required for auth persistence")
        self.engine: Engine = create_engine(self._sync_url(database_url), pool_pre_ping=True)
        Base.metadata.create_all(self.engine)

    def find_by_email(self, email: str) -> AuthUserRow | None:
        with Session(self.engine) as session:
            return session.query(AuthUserRow).filter(AuthUserRow.email == email, AuthUserRow.is_active.is_(True)).first()

    def create_user(self, *, email: str, password_hash: str, roles: list[str] | None = None) -> AuthUserRow:
        user = AuthUserRow(
            id=str(uuid4()),
            email=email,
            password_hash=password_hash,
            roles=roles or ["customer"],
            is_active=True,
        )
        with Session(self.engine) as session:
            session.add(user)
            session.commit()
            session.refresh(user)
            return user

    def _sync_url(self, database_url: str) -> str:
        return database_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
