from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.cart import Cart, CartItem
from app.models.enums import RestaurantStatus
from app.models.menu import MenuItem
from app.models.restaurant import Restaurant
from app.models.user import User
from app.schemas.cart import CartRead
from app.services.pricing import calculate_total


def _cart_query(customer_id: str):
    return (
        select(Cart)
        .where(Cart.customer_id == customer_id)
        .options(selectinload(Cart.items).selectinload(CartItem.menu_item))
    )


def get_or_create_cart(db: Session, customer: User) -> Cart:
    cart = db.scalar(_cart_query(customer.id))
    if cart:
        return cart
    cart = Cart(customer_id=customer.id)
    db.add(cart)
    db.commit()
    db.refresh(cart)
    return db.scalar(_cart_query(customer.id)) or cart


def get_cart(db: Session, customer: User) -> Cart:
    return get_or_create_cart(db, customer)


def serialize_cart(db: Session, cart: Cart) -> CartRead:
    items = []
    subtotal = 0
    for cart_item in cart.items:
        menu_item = cart_item.menu_item
        if not menu_item:
            continue
        line_total = menu_item.price_cents * cart_item.quantity
        subtotal += line_total
        items.append(
            {
                "id": cart_item.id,
                "menu_item_id": menu_item.id,
                "restaurant_id": menu_item.restaurant_id,
                "name": menu_item.name,
                "unit_price_cents": menu_item.price_cents,
                "quantity": cart_item.quantity,
                "line_total_cents": line_total,
            }
        )

    delivery_fee = 0
    if cart.restaurant_id and items:
        restaurant = db.get(Restaurant, cart.restaurant_id)
        delivery_fee = restaurant.delivery_fee_cents if restaurant else 0
    prices = calculate_total(subtotal, delivery_fee) if items else calculate_total(0, 0)
    return CartRead(
        id=cart.id,
        restaurant_id=cart.restaurant_id,
        items=items,
        subtotal_cents=prices.subtotal_cents,
        delivery_fee_cents=prices.delivery_fee_cents,
        tax_cents=prices.tax_cents,
        total_cents=prices.total_cents,
    )


def add_item(db: Session, customer: User, menu_item_id: str, quantity: int) -> Cart:
    menu_item = db.get(MenuItem, menu_item_id)
    if not menu_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu item not found")
    if not menu_item.is_available:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Menu item is unavailable")
    restaurant = db.get(Restaurant, menu_item.restaurant_id)
    if not restaurant or restaurant.status != RestaurantStatus.OPEN.value:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Restaurant is closed")

    cart = get_or_create_cart(db, customer)
    if cart.restaurant_id and cart.restaurant_id != menu_item.restaurant_id and cart.items:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cart can contain items from only one restaurant")
    cart.restaurant_id = menu_item.restaurant_id

    existing = next((item for item in cart.items if item.menu_item_id == menu_item.id), None)
    if existing:
        existing.quantity = min(existing.quantity + quantity, 20)
    else:
        db.add(CartItem(cart_id=cart.id, menu_item_id=menu_item.id, quantity=quantity))
    db.commit()
    db.expire_all()
    return get_cart(db, customer)


def update_item(db: Session, customer: User, cart_item_id: str, quantity: int) -> Cart:
    cart = get_cart(db, customer)
    cart_item = next((item for item in cart.items if item.id == cart_item_id), None)
    if not cart_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found")
    cart_item.quantity = quantity
    db.commit()
    db.expire_all()
    return get_cart(db, customer)


def remove_item(db: Session, customer: User, cart_item_id: str) -> Cart:
    cart = get_cart(db, customer)
    cart_item = next((item for item in cart.items if item.id == cart_item_id), None)
    if not cart_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found")
    db.delete(cart_item)
    db.commit()
    db.expire_all()
    refreshed = get_cart(db, customer)
    if not refreshed.items:
        refreshed.restaurant_id = None
        db.commit()
        db.expire_all()
        refreshed = get_cart(db, customer)
    return refreshed


def clear_cart(db: Session, customer: User) -> Cart:
    cart = get_cart(db, customer)
    for item in list(cart.items):
        db.delete(item)
    cart.restaurant_id = None
    db.commit()
    db.expire_all()
    return get_cart(db, customer)
