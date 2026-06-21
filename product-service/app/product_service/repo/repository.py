from __future__ import annotations

from dataclasses import fields
from datetime import datetime
from typing import Any

from core_common.models import GridColumn, GridParams, PagedResponse
from product_service.schemas import Product

try:
    from sqlalchemy import DateTime, Integer, String, create_engine, func, select
    from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column
    from sqlalchemy.engine import Engine
except ModuleNotFoundError:
    create_engine = None
    DateTime = Integer = String = lambda *args, **kwargs: object()  # type: ignore[assignment]
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


class ProductRow(Base):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False, default="")
    price: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rating: Mapped[float] = mapped_column(nullable=False, default=4.5)
    image: Mapped[str] = mapped_column(String, nullable=False, default="")
    accent: Mapped[str] = mapped_column(String, nullable=False, default="#0e5d4e")
    created_by: Mapped[str | None] = mapped_column(String)
    updated_by: Mapped[str | None] = mapped_column(String)
    deleted_by: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)


class ProductRepository:
    _sortable = {
        "id": ProductRow.id,
        "name": ProductRow.name,
        "category": ProductRow.category,
        "price": ProductRow.price,
        "stock": ProductRow.stock,
        "rating": ProductRow.rating,
        "created_at": ProductRow.created_at,
    }

    def __init__(self, database_url: str) -> None:
        if create_engine is None:
            raise RuntimeError("sqlalchemy is required when PRODUCT_DATABASE_URL is configured")
        self.engine: Engine = create_engine(database_url, pool_pre_ping=True)
        Base.metadata.create_all(self.engine)

    def add(self, product: Product) -> Product:
        with Session(self.engine) as session:
            session.merge(self._to_row(product))
            session.commit()
        return product

    def get(self, product_id: str) -> Product | None:
        with Session(self.engine) as session:
            row = session.get(ProductRow, product_id)
            if row is None or row.deleted_at is not None:
                return None
            return self._from_row(row)

    def soft_delete(self, product_id: str, *, deleted_by: str | None = None) -> Product | None:
        product = self.get(product_id)
        if product is None:
            return None
        product.soft_delete(deleted_by)
        self.add(product)
        return product

    def list(
        self,
        params: GridParams | None = None,
        *,
        columns: list[GridColumn] | None = None,
        actions: list[dict[str, Any]] | None = None,
    ) -> PagedResponse[Product]:
        params = params or GridParams()
        with Session(self.engine) as session:
            query = select(ProductRow).where(ProductRow.deleted_at.is_(None))
            count_query = select(func.count()).select_from(ProductRow).where(ProductRow.deleted_at.is_(None))
            if params.filters.get("category"):
                query = query.where(ProductRow.category.ilike(str(params.filters["category"])))
                count_query = count_query.where(ProductRow.category.ilike(str(params.filters["category"])))
            order_column = self._sortable.get(params.sort_by or "", ProductRow.name)
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

    def _to_row(self, product: Product) -> ProductRow:
        payload = {field.name: getattr(product, field.name) for field in fields(Product)}
        return ProductRow(**payload)

    def _from_row(self, row: ProductRow) -> Product:
        return Product(
            id=row.id,
            name=row.name,
            category=row.category,
            description=row.description,
            price=row.price,
            stock=row.stock,
            rating=row.rating,
            image=row.image,
            accent=row.accent,
            created_at=row.created_at,
            updated_at=row.updated_at,
            deleted_at=row.deleted_at,
            created_by=row.created_by,
            updated_by=row.updated_by,
            deleted_by=row.deleted_by,
            is_active=row.is_active,
        )
