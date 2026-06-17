from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import require_customer
from app.core.database import get_db
from app.models.user import User
from app.schemas.cart import CartItemAdd, CartItemUpdate, CartRead
from app.schemas.common import APIMessage
from app.services.cart_service import add_item, clear_cart, get_cart, remove_item, serialize_cart, update_item

router = APIRouter(prefix="/cart", tags=["cart"])


@router.get("", response_model=CartRead)
def read_cart(db: Session = Depends(get_db), customer: User = Depends(require_customer)) -> CartRead:
    return serialize_cart(db, get_cart(db, customer))


@router.post("/items", response_model=CartRead, status_code=status.HTTP_201_CREATED)
def add_cart_item(payload: CartItemAdd, db: Session = Depends(get_db), customer: User = Depends(require_customer)) -> CartRead:
    cart = add_item(db, customer, payload.menu_item_id, payload.quantity)
    return serialize_cart(db, cart)


@router.patch("/items/{cart_item_id}", response_model=CartRead)
def update_cart_item(
    cart_item_id: str,
    payload: CartItemUpdate,
    db: Session = Depends(get_db),
    customer: User = Depends(require_customer),
) -> CartRead:
    cart = update_item(db, customer, cart_item_id, payload.quantity)
    return serialize_cart(db, cart)


@router.delete("/items/{cart_item_id}", response_model=CartRead)
def remove_cart_item(cart_item_id: str, db: Session = Depends(get_db), customer: User = Depends(require_customer)) -> CartRead:
    cart = remove_item(db, customer, cart_item_id)
    return serialize_cart(db, cart)


@router.delete("", response_model=CartRead)
def clear_cart_endpoint(db: Session = Depends(get_db), customer: User = Depends(require_customer)) -> CartRead:
    cart = clear_cart(db, customer)
    return serialize_cart(db, cart)
