from __future__ import annotations

from sqlalchemy import ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IdMixin, TimestampMixin


class Cart(IdMixin, TimestampMixin, Base):
    __tablename__ = "carts"

    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), unique=True, nullable=False, index=True)
    restaurant_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("restaurants.id"), nullable=True, index=True)

    customer = relationship("User", back_populates="cart")
    restaurant = relationship("Restaurant")
    items = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")


class CartItem(IdMixin, TimestampMixin, Base):
    __tablename__ = "cart_items"
    __table_args__ = (
        UniqueConstraint("cart_id", "menu_item_id", name="uq_cart_menu_item"),
    )

    cart_id: Mapped[str] = mapped_column(String(36), ForeignKey("carts.id"), nullable=False, index=True)
    menu_item_id: Mapped[str] = mapped_column(String(36), ForeignKey("menu_items.id"), nullable=False, index=True)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    cart = relationship("Cart", back_populates="items")
    menu_item = relationship("MenuItem", back_populates="cart_items")


Index("ix_cart_items_cart_item", CartItem.cart_id, CartItem.menu_item_id)
