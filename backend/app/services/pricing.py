from __future__ import annotations

from dataclasses import dataclass

from app.core.config import get_settings


@dataclass(frozen=True)
class PriceBreakdown:
    subtotal_cents: int
    delivery_fee_cents: int
    tax_cents: int
    discount_cents: int
    total_cents: int


def calculate_tax_cents(subtotal_cents: int) -> int:
    settings = get_settings()
    return (subtotal_cents * settings.TAX_RATE_BPS + 9999) // 10000


def calculate_total(subtotal_cents: int, delivery_fee_cents: int, discount_cents: int = 0) -> PriceBreakdown:
    tax_cents = calculate_tax_cents(subtotal_cents)
    total = max(0, subtotal_cents + delivery_fee_cents + tax_cents - discount_cents)
    return PriceBreakdown(
        subtotal_cents=subtotal_cents,
        delivery_fee_cents=delivery_fee_cents,
        tax_cents=tax_cents,
        discount_cents=discount_cents,
        total_cents=total,
    )
