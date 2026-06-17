from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import RestaurantStatus


class RestaurantCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=1000)
    cuisine: str = Field(min_length=2, max_length=80)
    address: str = Field(min_length=5, max_length=255)
    city: str = Field(min_length=2, max_length=80)
    delivery_fee_cents: int = Field(default=3000, ge=0, le=100000)
    min_order_amount_cents: int = Field(default=0, ge=0, le=500000)
    latitude: float | None = None
    longitude: float | None = None


class RestaurantUpdate(BaseModel):
    status: RestaurantStatus | None = None
    description: str | None = Field(default=None, max_length=1000)
    delivery_fee_cents: int | None = Field(default=None, ge=0, le=100000)
    min_order_amount_cents: int | None = Field(default=None, ge=0, le=500000)


class RestaurantRead(BaseModel):
    id: str
    owner_id: str
    name: str
    description: str | None
    cuisine: str
    address: str
    city: str
    status: RestaurantStatus
    rating: float
    delivery_fee_cents: int
    min_order_amount_cents: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MenuItemCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=1000)
    category: str = Field(default="MAIN", min_length=2, max_length=60)
    price_cents: int = Field(ge=100, le=200000)
    is_available: bool = True


class MenuItemUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=1000)
    category: str | None = Field(default=None, min_length=2, max_length=60)
    price_cents: int | None = Field(default=None, ge=100, le=200000)
    is_available: bool | None = None


class MenuItemRead(BaseModel):
    id: str
    restaurant_id: str
    name: str
    description: str | None
    category: str
    price_cents: int
    is_available: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RestaurantWithMenu(RestaurantRead):
    menu_items: list[MenuItemRead] = []
