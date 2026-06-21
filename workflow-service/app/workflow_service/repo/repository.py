from __future__ import annotations

from datetime import datetime
from typing import Any

try:
    from sqlalchemy import DateTime, JSON, String, create_engine, func, select
    from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column
    from sqlalchemy.engine import Engine
except ModuleNotFoundError:
    create_engine = None
    DateTime = JSON = String = lambda *args, **kwargs: object()  # type: ignore[assignment]
    class _Func:
        @staticmethod
        def now() -> object:
            return object()
    func = _Func()  # type: ignore[assignment]
    select = None  # type: ignore[assignment]
    DeclarativeBase = object  # type: ignore[assignment]
    Mapped = Any  # type: ignore[assignment]
    Session = None  # type: ignore[assignment]
    mapped_column = lambda *args, **kwargs: None  # type: ignore[assignment]
    Engine = Any  # type: ignore[misc,assignment]


class Base(DeclarativeBase):
    pass


class WorkflowTaskRow(Base):
    __tablename__ = "workflow_tasks"

    code: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    service: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False, default="")
    inputs: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    outputs: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class TaskRepository:
    def __init__(self, database_url: str) -> None:
        if create_engine is None:
            raise RuntimeError("sqlalchemy is required when WORKFLOW_DATABASE_URL is configured")
        self.engine: Engine = create_engine(database_url, pool_pre_ping=True)
        Base.metadata.create_all(self.engine)

    def list(self) -> list[dict]:
        with Session(self.engine) as session:
            rows = session.scalars(select(WorkflowTaskRow).order_by(WorkflowTaskRow.code)).all()
        return [self._from_row(row) for row in rows]

    def get(self, code: str) -> dict | None:
        with Session(self.engine) as session:
            row = session.get(WorkflowTaskRow, code)
        return self._from_row(row) if row else None

    def _from_row(self, row: WorkflowTaskRow) -> dict:
        return {
            "code": row.code,
            "name": row.name,
            "service": row.service,
            "status": row.status,
            "description": row.description,
            "inputs": list(row.inputs),
            "outputs": list(row.outputs),
        }
