from __future__ import annotations

from dataclasses import dataclass

from core_common.models import AuditEntity


@dataclass(slots=True)
class Product(AuditEntity):
    name: str = ""
    category: str = ""
    price: int = 0
    stock: int = 0


@dataclass(frozen=True, slots=True)
class ReservationResult:
    product_id: str
    quantity: int
    reserved: bool
