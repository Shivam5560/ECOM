from __future__ import annotations

from dataclasses import dataclass

from core_common.models import AuditEntity


@dataclass(slots=True)
class Product(AuditEntity):
    name: str = ""
    category: str = ""
    description: str = ""
    price: int = 0
    stock: int = 0
    rating: float = 4.5
    image: str = ""
    accent: str = "#0e5d4e"


@dataclass(frozen=True, slots=True)
class ReservationResult:
    product_id: str
    quantity: int
    reserved: bool


@dataclass(frozen=True, slots=True)
class OrderReservationResult:
    reservation_id: str
    order_id: str
    reserved: bool
    lines: list[dict]
    reason: str = ""


@dataclass(frozen=True, slots=True)
class ReservationCommitResult:
    reservation_id: str
    committed: bool


@dataclass(frozen=True, slots=True)
class ReservationReleaseResult:
    reservation_id: str
    released: bool
