from __future__ import annotations

from sqlalchemy import ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IdMixin, TimestampMixin
from app.models.enums import RestaurantStatus


class Restaurant(IdMixin, TimestampMixin, Base):
    __tablename__ = "restaurants"

    owner_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    cuisine: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), default=RestaurantStatus.OPEN.value, nullable=False, index=True)
    rating: Mapped[float] = mapped_column(Numeric(3, 2), default=4.50, nullable=False)
    delivery_fee_cents: Mapped[int] = mapped_column(Integer, default=3000, nullable=False)
    min_order_amount_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    latitude: Mapped[float | None] = mapped_column(Numeric(9, 6), nullable=True)
    longitude: Mapped[float | None] = mapped_column(Numeric(9, 6), nullable=True)

    owner = relationship("User", back_populates="restaurants")
    menu_items = relationship("MenuItem", back_populates="restaurant", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="restaurant")


Index("ix_restaurants_city_cuisine_status", Restaurant.city, Restaurant.cuisine, Restaurant.status)
