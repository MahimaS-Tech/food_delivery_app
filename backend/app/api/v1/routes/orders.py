from __future__ import annotations

from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_customer
from app.core.database import get_db
from app.models.user import User
from app.schemas.order import DeliveryAssignRequest, OrderCreate, OrderRead, OrderStatusUpdate
from app.services.order_service import assign_delivery_partner, create_order_from_cart, get_order_for_user, list_orders, update_order_status

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
def create_order(
    payload: OrderCreate,
    idempotency_key: str = Header(..., alias="X-Idempotency-Key", min_length=8, max_length=120),
    db: Session = Depends(get_db),
    customer: User = Depends(require_customer),
):
    return create_order_from_cart(
        db,
        customer,
        delivery_address=payload.delivery_address,
        payment_method=payload.payment_method,
        idempotency_key=idempotency_key,
    )


@router.get("", response_model=list[OrderRead])
def read_orders(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return list_orders(db, user, limit, offset)


@router.get("/{order_id}", response_model=OrderRead)
def read_order(order_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return get_order_for_user(db, user, order_id)


@router.patch("/{order_id}/status", response_model=OrderRead)
def patch_order_status(
    order_id: str,
    payload: OrderStatusUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return update_order_status(db, user, order_id, payload.status)


@router.post("/{order_id}/assign-delivery", response_model=OrderRead)
def assign_delivery(
    order_id: str,
    payload: DeliveryAssignRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return assign_delivery_partner(db, user, order_id, payload.partner_id)
