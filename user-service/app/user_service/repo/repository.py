from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from user_service.schemas import UserProfile

try:
    from sqlalchemy import DateTime, String, create_engine, select
    from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column
    from sqlalchemy.engine import Engine
except ModuleNotFoundError:
    create_engine = None
    DateTime = String = lambda *args, **kwargs: object()  # type: ignore[assignment]
    DeclarativeBase = object  # type: ignore[assignment]
    Mapped = Any  # type: ignore[assignment]
    Session = None  # type: ignore[assignment]
    mapped_column = lambda *args, **kwargs: None  # type: ignore[assignment]
    select = None  # type: ignore[assignment]
    Engine = Any  # type: ignore[misc,assignment]


class Base(DeclarativeBase):
    pass


class UserProfileRow(Base):
    __tablename__ = "user_profiles"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    auth_subject: Mapped[str] = mapped_column(String, nullable=False, index=True)
    email: Mapped[str | None] = mapped_column(String)
    display_name: Mapped[str] = mapped_column(String, nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String)
    phone: Mapped[str | None] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class UserProfileRepository:
    def __init__(self, database_url: str) -> None:
        if create_engine is None:
            raise RuntimeError("sqlalchemy is required when USER_DATABASE_URL is configured")
        self.engine: Engine = create_engine(database_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://"), pool_pre_ping=True)
        Base.metadata.create_all(self.engine)

    def add(self, profile: UserProfile) -> UserProfile:
        with Session(self.engine) as session:
            session.merge(self._to_row(profile))
            session.commit()
        return profile

    def list(self) -> list[UserProfile]:
        with Session(self.engine) as session:
            rows = session.scalars(
                select(UserProfileRow).where(UserProfileRow.deleted_at.is_(None))
            ).all()
        return [self._from_row(row) for row in rows]

    def get(self, profile_id: str) -> UserProfile | None:
        with Session(self.engine) as session:
            row = session.get(UserProfileRow, profile_id)
            if row is None or row.deleted_at is not None:
                return None
            return self._from_row(row)

    def soft_delete(self, profile_id: str) -> UserProfile | None:
        profile = self.get(profile_id)
        if profile is None:
            return None
        profile.deleted_at = datetime.now(timezone.utc)
        profile.is_active = False
        self.add(profile)
        return profile

    def _to_row(self, profile: UserProfile) -> UserProfileRow:
        return UserProfileRow(
            id=profile.id,
            auth_subject=profile.auth_subject,
            email=profile.email,
            display_name=profile.display_name,
            password_hash=profile.password_hash,
            phone=profile.phone,
            is_active=profile.is_active,
            deleted_at=profile.deleted_at,
        )

    def _from_row(self, row: UserProfileRow) -> UserProfile:
        return UserProfile(
            id=row.id,
            auth_subject=row.auth_subject,
            email=row.email,
            display_name=row.display_name,
            password_hash=row.password_hash,
            phone=row.phone,
            is_active=row.is_active,
            deleted_at=row.deleted_at,
        )
