from __future__ import annotations

from pydantic import BaseModel, Field


class CartItemAdd(BaseModel):
    menu_item_id: str
    quantity: int = Field(ge=1, le=20)


class CartItemUpdate(BaseModel):
    quantity: int = Field(ge=1, le=20)


class CartItemRead(BaseModel):
    id: str
    menu_item_id: str
    restaurant_id: str
    name: str
    unit_price_cents: int
    quantity: int
    line_total_cents: int


class CartRead(BaseModel):
    id: str | None
    restaurant_id: str | None
    items: list[CartItemRead]
    subtotal_cents: int
    delivery_fee_cents: int
    tax_cents: int
    total_cents: int
