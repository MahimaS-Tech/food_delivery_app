from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models.cart import Cart, CartItem
from app.models.delivery import DeliveryAssignment
from app.models.enums import OrderStatus, PaymentMethod, PaymentStatus, RestaurantStatus, UserRole
from app.models.order import Order, OrderItem
from app.models.restaurant import Restaurant
from app.models.user import User
from app.services.outbox_service import add_outbox_event
from app.services.pricing import calculate_total

ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    OrderStatus.PLACED.value: {OrderStatus.ACCEPTED.value, OrderStatus.CANCELLED.value},
    OrderStatus.ACCEPTED.value: {OrderStatus.PREPARING.value, OrderStatus.CANCELLED.value},
    OrderStatus.PREPARING.value: {OrderStatus.OUT_FOR_DELIVERY.value, OrderStatus.CANCELLED.value},
    OrderStatus.OUT_FOR_DELIVERY.value: {OrderStatus.DELIVERED.value},
    OrderStatus.DELIVERED.value: set(),
    OrderStatus.CANCELLED.value: set(),
}


def _cart_for_checkout_query(customer_id: str):
    return (
        select(Cart)
        .where(Cart.customer_id == customer_id)
        .options(selectinload(Cart.items).selectinload(CartItem.menu_item))
    )


def get_order_or_404(db: Session, order_id: str) -> Order:
    order = db.scalar(select(Order).where(Order.id == order_id).options(selectinload(Order.items)))
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order


def ensure_can_view_order(db: Session, user: User, order: Order) -> None:
    if user.role == UserRole.ADMIN.value:
        return
    if user.role == UserRole.CUSTOMER.value and order.customer_id == user.id:
        return
    if user.role == UserRole.DELIVERY_PARTNER.value and order.delivery_partner_id == user.id:
        return
    if user.role == UserRole.RESTAURANT_OWNER.value:
        restaurant = db.get(Restaurant, order.restaurant_id)
        if restaurant and restaurant.owner_id == user.id:
            return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to view this order")


def _ensure_order_actor_can_mutate(db: Session, user: User, order: Order, next_status: str) -> None:
    if user.role == UserRole.ADMIN.value:
        return
    if user.role == UserRole.RESTAURANT_OWNER.value:
        restaurant = db.get(Restaurant, order.restaurant_id)
        if restaurant and restaurant.owner_id == user.id and next_status in {
            OrderStatus.ACCEPTED.value,
            OrderStatus.PREPARING.value,
            OrderStatus.OUT_FOR_DELIVERY.value,
            OrderStatus.CANCELLED.value,
        }:
            return
    if user.role == UserRole.DELIVERY_PARTNER.value and order.delivery_partner_id == user.id and next_status in {
        OrderStatus.OUT_FOR_DELIVERY.value,
        OrderStatus.DELIVERED.value,
    }:
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to update this order")


def create_order_from_cart(
    db: Session,
    customer: User,
    *,
    delivery_address: str,
    payment_method: PaymentMethod,
    idempotency_key: str,
) -> Order:
    existing = db.scalar(
        select(Order)
        .where(Order.customer_id == customer.id, Order.idempotency_key == idempotency_key)
        .options(selectinload(Order.items))
    )
    if existing:
        return existing

    cart = db.scalar(_cart_for_checkout_query(customer.id))
    if not cart or not cart.items:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cart is empty")
    if not cart.restaurant_id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cart restaurant is missing")

    restaurant = db.get(Restaurant, cart.restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found")
    if restaurant.status != RestaurantStatus.OPEN.value:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Restaurant is closed")

    subtotal = 0
    order_items: list[OrderItem] = []
    for cart_item in cart.items:
        menu_item = cart_item.menu_item
        if not menu_item or not menu_item.is_available:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cart contains unavailable item")
        if menu_item.restaurant_id != cart.restaurant_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cart contains items from multiple restaurants")
        line_total = menu_item.price_cents * cart_item.quantity
        subtotal += line_total
        order_items.append(
            OrderItem(
                menu_item_id=menu_item.id,
                item_name_snapshot=menu_item.name,
                unit_price_cents=menu_item.price_cents,
                quantity=cart_item.quantity,
                line_total_cents=line_total,
            )
        )

    if subtotal < restaurant.min_order_amount_cents:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Minimum order amount not reached")

    price = calculate_total(subtotal, restaurant.delivery_fee_cents)
    order = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        status=OrderStatus.PLACED.value,
        payment_status=PaymentStatus.AUTHORIZED.value,
        payment_method=payment_method.value if hasattr(payment_method, "value") else str(payment_method),
        subtotal_cents=price.subtotal_cents,
        delivery_fee_cents=price.delivery_fee_cents,
        tax_cents=price.tax_cents,
        discount_cents=price.discount_cents,
        total_cents=price.total_cents,
        delivery_address=delivery_address,
        idempotency_key=idempotency_key,
    )
    db.add(order)
    db.flush()
    for item in order_items:
        item.order_id = order.id
        db.add(item)

    for cart_item in list(cart.items):
        db.delete(cart_item)
    cart.restaurant_id = None

    add_outbox_event(
        db,
        aggregate_type="Order",
        aggregate_id=order.id,
        event_type="order.placed",
        payload={
            "order_id": order.id,
            "customer_id": customer.id,
            "restaurant_id": restaurant.id,
            "total_cents": price.total_cents,
        },
    )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.scalar(
            select(Order)
            .where(Order.customer_id == customer.id, Order.idempotency_key == idempotency_key)
            .options(selectinload(Order.items))
        )
        if existing:
            return existing
        raise
    return get_order_or_404(db, order.id)


def list_orders(db: Session, user: User, limit: int, offset: int) -> list[Order]:
    limit = min(max(limit, 1), 100)
    offset = max(offset, 0)
    stmt = select(Order).options(selectinload(Order.items)).order_by(Order.created_at.desc()).limit(limit).offset(offset)
    if user.role == UserRole.CUSTOMER.value:
        stmt = stmt.where(Order.customer_id == user.id)
    elif user.role == UserRole.RESTAURANT_OWNER.value:
        stmt = stmt.join(Restaurant, Restaurant.id == Order.restaurant_id).where(Restaurant.owner_id == user.id)
    elif user.role == UserRole.DELIVERY_PARTNER.value:
        stmt = stmt.where(Order.delivery_partner_id == user.id)
    elif user.role == UserRole.ADMIN.value:
        pass
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
    return list(db.scalars(stmt).all())


def get_order_for_user(db: Session, user: User, order_id: str) -> Order:
    order = get_order_or_404(db, order_id)
    ensure_can_view_order(db, user, order)
    return order


def update_order_status(db: Session, user: User, order_id: str, next_status: OrderStatus) -> Order:
    order = get_order_or_404(db, order_id)
    next_value = next_status.value
    if next_value not in ALLOWED_TRANSITIONS.get(order.status, set()):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Invalid status transition from {order.status} to {next_value}")
    _ensure_order_actor_can_mutate(db, user, order, next_value)
    order.status = next_value
    if next_value == OrderStatus.CANCELLED.value and order.payment_status == PaymentStatus.AUTHORIZED.value:
        order.payment_status = PaymentStatus.REFUNDED.value
    add_outbox_event(
        db,
        aggregate_type="Order",
        aggregate_id=order.id,
        event_type="order.status_changed",
        payload={"order_id": order.id, "status": next_value},
    )
    db.commit()
    return get_order_or_404(db, order.id)


def assign_delivery_partner(db: Session, user: User, order_id: str, partner_id: str) -> Order:
    order = get_order_or_404(db, order_id)
    if user.role != UserRole.ADMIN.value:
        restaurant = db.get(Restaurant, order.restaurant_id)
        if user.role != UserRole.RESTAURANT_OWNER.value or not restaurant or restaurant.owner_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Restaurant owner or admin required")
    partner = db.get(User, partner_id)
    if not partner or partner.role != UserRole.DELIVERY_PARTNER.value:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery partner not found")
    order.delivery_partner_id = partner.id
    assignment = db.scalar(select(DeliveryAssignment).where(DeliveryAssignment.order_id == order.id))
    if not assignment:
        db.add(DeliveryAssignment(order_id=order.id, partner_id=partner.id))
    else:
        assignment.partner_id = partner.id
    add_outbox_event(
        db,
        aggregate_type="Order",
        aggregate_id=order.id,
        event_type="order.delivery_assigned",
        payload={"order_id": order.id, "partner_id": partner.id},
    )
    db.commit()
    return get_order_or_404(db, order.id)
