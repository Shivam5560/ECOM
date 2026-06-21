from __future__ import annotations

from dataclasses import fields
from datetime import datetime
from typing import Any

from core_common.models import GridColumn, GridParams, PagedResponse
from order_service.schemas import Order

try:
    from sqlalchemy import DateTime, Integer, JSON, String, create_engine, func, select
    from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column
    from sqlalchemy.engine import Engine
except ModuleNotFoundError:
    create_engine = None
    DateTime = Integer = JSON = String = lambda *args, **kwargs: object()  # type: ignore[assignment]
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


class OrderRow(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    lines: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list)
    created_by: Mapped[str | None] = mapped_column(String)
    updated_by: Mapped[str | None] = mapped_column(String)
    deleted_by: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)


class OrderRepository:
    _sortable = {
        "id": OrderRow.id,
        "status": OrderRow.status,
        "total": OrderRow.total,
        "created_at": OrderRow.created_at,
    }

    def __init__(self, database_url: str) -> None:
        if create_engine is None:
            raise RuntimeError("sqlalchemy is required when ORDER_DATABASE_URL is configured")
        self.engine: Engine = create_engine(database_url, pool_pre_ping=True)
        Base.metadata.create_all(self.engine)

    def add(self, order: Order) -> Order:
        with Session(self.engine) as session:
            session.merge(self._to_row(order))
            session.commit()
        return order

    def list(
        self,
        params: GridParams | None = None,
        *,
        columns: list[GridColumn] | None = None,
        actions: list[dict[str, Any]] | None = None,
    ) -> PagedResponse[Order]:
        params = params or GridParams()
        with Session(self.engine) as session:
            query = select(OrderRow).where(OrderRow.deleted_at.is_(None))
            count_query = select(func.count()).select_from(OrderRow).where(OrderRow.deleted_at.is_(None))
            if params.filters.get("status"):
                query = query.where(OrderRow.status.ilike(str(params.filters["status"])))
                count_query = count_query.where(OrderRow.status.ilike(str(params.filters["status"])))
            order_column = self._sortable.get(params.sort_by or "", OrderRow.created_at)
            if params.order == "desc":
                order_column = order_column.desc()
            rows = session.scalars(query.order_by(order_column).limit(params.size).offset(params.offset)).all()
            total = session.scalar(count_query) or 0
        return PagedResponse(
            items=[self._from_row(row) for row in rows],
            total=int(total),
            page=params.page,
            size=params.size,
            columns=columns or [],
            actions=actions,
        )

    def _to_row(self, order: Order) -> OrderRow:
        payload = {field.name: getattr(order, field.name) for field in fields(Order)}
        return OrderRow(**payload)

    def _from_row(self, row: OrderRow) -> Order:
        return Order(
            id=row.id,
            user_id=row.user_id,
            status=row.status,
            total=row.total,
            lines=list(row.lines),
            created_at=row.created_at,
            updated_at=row.updated_at,
            deleted_at=row.deleted_at,
            created_by=row.created_by,
            updated_by=row.updated_by,
            deleted_by=row.deleted_by,
            is_active=row.is_active,
        )
