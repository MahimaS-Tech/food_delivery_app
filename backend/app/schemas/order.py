from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import OrderStatus, PaymentMethod, PaymentStatus


class OrderCreate(BaseModel):
    delivery_address: str = Field(min_length=8, max_length=1000)
    payment_method: PaymentMethod = PaymentMethod.COD


class OrderStatusUpdate(BaseModel):
    status: OrderStatus


class DeliveryAssignRequest(BaseModel):
    partner_id: str


class OrderItemRead(BaseModel):
    id: str
    menu_item_id: str
    item_name_snapshot: str
    unit_price_cents: int
    quantity: int
    line_total_cents: int

    model_config = ConfigDict(from_attributes=True)


class OrderRead(BaseModel):
    id: str
    customer_id: str
    restaurant_id: str
    delivery_partner_id: str | None
    status: OrderStatus
    payment_status: PaymentStatus
    payment_method: PaymentMethod
    subtotal_cents: int
    delivery_fee_cents: int
    tax_cents: int
    discount_cents: int
    total_cents: int
    delivery_address: str
    idempotency_key: str
    created_at: datetime
    updated_at: datetime
    items: list[OrderItemRead]

    model_config = ConfigDict(from_attributes=True)
