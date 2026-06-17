from __future__ import annotations

from sqlalchemy import ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IdMixin, TimestampMixin
from app.models.enums import OrderStatus, PaymentMethod, PaymentStatus


class Order(IdMixin, TimestampMixin, Base):
    __tablename__ = "orders"
    __table_args__ = (
        UniqueConstraint("customer_id", "idempotency_key", name="uq_order_customer_idempotency"),
    )

    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    restaurant_id: Mapped[str] = mapped_column(String(36), ForeignKey("restaurants.id"), nullable=False, index=True)
    delivery_partner_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True, index=True)

    status: Mapped[str] = mapped_column(String(40), default=OrderStatus.PLACED.value, nullable=False, index=True)
    payment_status: Mapped[str] = mapped_column(String(30), default=PaymentStatus.PENDING.value, nullable=False, index=True)
    payment_method: Mapped[str] = mapped_column(String(20), default=PaymentMethod.COD.value, nullable=False)

    subtotal_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    delivery_fee_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    tax_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    discount_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_cents: Mapped[int] = mapped_column(Integer, nullable=False)

    delivery_address: Mapped[str] = mapped_column(Text, nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(120), nullable=False)

    customer = relationship("User", back_populates="orders", foreign_keys=[customer_id])
    delivery_partner = relationship("User", foreign_keys=[delivery_partner_id])
    restaurant = relationship("Restaurant", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(IdMixin, TimestampMixin, Base):
    __tablename__ = "order_items"

    order_id: Mapped[str] = mapped_column(String(36), ForeignKey("orders.id"), nullable=False, index=True)
    menu_item_id: Mapped[str] = mapped_column(String(36), ForeignKey("menu_items.id"), nullable=False, index=True)
    item_name_snapshot: Mapped[str] = mapped_column(String(120), nullable=False)
    unit_price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    line_total_cents: Mapped[int] = mapped_column(Integer, nullable=False)

    order = relationship("Order", back_populates="items")
    menu_item = relationship("MenuItem", back_populates="order_items")


Index("ix_orders_customer_status", Order.customer_id, Order.status)
Index("ix_orders_restaurant_status", Order.restaurant_id, Order.status)
