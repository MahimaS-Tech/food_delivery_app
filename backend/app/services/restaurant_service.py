from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.cache import cache
from app.core.config import get_settings
from app.models.enums import RestaurantStatus, UserRole
from app.models.menu import MenuItem
from app.models.restaurant import Restaurant
from app.models.user import User
from app.schemas.restaurant import MenuItemCreate, MenuItemRead, MenuItemUpdate, RestaurantCreate, RestaurantRead, RestaurantUpdate


def _cache_key(city: str | None, cuisine: str | None, q: str | None, open_only: bool, limit: int, offset: int) -> str:
    return f"restaurants:{city or ''}:{cuisine or ''}:{q or ''}:{open_only}:{limit}:{offset}".lower()


def ensure_owner_or_admin(user: User, restaurant: Restaurant) -> None:
    if user.role == UserRole.ADMIN.value:
        return
    if user.role == UserRole.RESTAURANT_OWNER.value and restaurant.owner_id == user.id:
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Restaurant owner or admin required")


def create_restaurant(db: Session, owner: User, payload: RestaurantCreate) -> Restaurant:
    restaurant = Restaurant(
        owner_id=owner.id,
        name=payload.name.strip(),
        description=payload.description,
        cuisine=payload.cuisine.strip(),
        address=payload.address.strip(),
        city=payload.city.strip(),
        delivery_fee_cents=payload.delivery_fee_cents,
        min_order_amount_cents=payload.min_order_amount_cents,
        latitude=payload.latitude,
        longitude=payload.longitude,
    )
    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)
    cache.delete_prefix("restaurants:")
    return restaurant


def list_restaurants(
    db: Session,
    *,
    city: str | None,
    cuisine: str | None,
    q: str | None,
    open_only: bool,
    limit: int,
    offset: int,
) -> list[dict]:
    settings = get_settings()
    limit = min(max(limit, 1), settings.MAX_PAGE_LIMIT)
    offset = max(offset, 0)
    key = _cache_key(city, cuisine, q, open_only, limit, offset)
    cached = cache.get_json(key)
    if cached is not None:
        return cached

    stmt = select(Restaurant).order_by(Restaurant.rating.desc(), Restaurant.name.asc()).limit(limit).offset(offset)
    if city:
        stmt = stmt.where(Restaurant.city.ilike(f"%{city}%"))
    if cuisine:
        stmt = stmt.where(Restaurant.cuisine.ilike(f"%{cuisine}%"))
    if q:
        stmt = stmt.where(or_(Restaurant.name.ilike(f"%{q}%"), Restaurant.description.ilike(f"%{q}%")))
    if open_only:
        stmt = stmt.where(Restaurant.status == RestaurantStatus.OPEN.value)

    restaurants = list(db.scalars(stmt).all())
    serialized = [RestaurantRead.model_validate(item).model_dump(mode="json") for item in restaurants]
    cache.set_json(key, serialized)
    return serialized


def get_restaurant_or_404(db: Session, restaurant_id: str) -> Restaurant:
    restaurant = db.get(Restaurant, restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found")
    return restaurant


def get_restaurant_with_menu(db: Session, restaurant_id: str) -> Restaurant:
    restaurant = db.scalar(
        select(Restaurant)
        .where(Restaurant.id == restaurant_id)
        .options(selectinload(Restaurant.menu_items))
    )
    if not restaurant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found")
    return restaurant


def update_restaurant(db: Session, user: User, restaurant_id: str, payload: RestaurantUpdate) -> Restaurant:
    restaurant = get_restaurant_or_404(db, restaurant_id)
    ensure_owner_or_admin(user, restaurant)
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        if value is not None:
            setattr(restaurant, key, value.value if hasattr(value, "value") else value)
    db.commit()
    db.refresh(restaurant)
    cache.delete_prefix("restaurants:")
    return restaurant


def create_menu_item(db: Session, user: User, restaurant_id: str, payload: MenuItemCreate) -> MenuItem:
    restaurant = get_restaurant_or_404(db, restaurant_id)
    ensure_owner_or_admin(user, restaurant)
    item = MenuItem(
        restaurant_id=restaurant.id,
        name=payload.name.strip(),
        description=payload.description,
        category=payload.category.strip().upper(),
        price_cents=payload.price_cents,
        is_available=payload.is_available,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    cache.delete_prefix("restaurants:")
    return item


def update_menu_item(db: Session, user: User, restaurant_id: str, item_id: str, payload: MenuItemUpdate) -> MenuItem:
    restaurant = get_restaurant_or_404(db, restaurant_id)
    ensure_owner_or_admin(user, restaurant)
    item = db.get(MenuItem, item_id)
    if not item or item.restaurant_id != restaurant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu item not found")
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        if value is not None:
            setattr(item, key, value)
    db.commit()
    db.refresh(item)
    cache.delete_prefix("restaurants:")
    return item


def list_menu_items(db: Session, restaurant_id: str, available_only: bool = True) -> list[MenuItem]:
    get_restaurant_or_404(db, restaurant_id)
    stmt = select(MenuItem).where(MenuItem.restaurant_id == restaurant_id).order_by(MenuItem.category.asc(), MenuItem.name.asc())
    if available_only:
        stmt = stmt.where(MenuItem.is_available.is_(True))
    return list(db.scalars(stmt).all())
