from __future__ import annotations

from sqlalchemy import select

from app.core.database import configure_database, create_schema, session_scope
from app.core.security import hash_password
from app.models.enums import UserRole
from app.models.menu import MenuItem
from app.models.restaurant import Restaurant
from app.models.user import User


def ensure_user(db, email: str, full_name: str, role: UserRole, password: str = "Password123") -> User:
    user = db.scalar(select(User).where(User.email == email))
    if user:
        return user
    user = User(email=email, full_name=full_name, role=role.value, password_hash=hash_password(password))
    db.add(user)
    db.flush()
    return user


def ensure_menu_item(db, restaurant: Restaurant, name: str, category: str, price_cents: int) -> MenuItem:
    item = db.scalar(select(MenuItem).where(MenuItem.restaurant_id == restaurant.id, MenuItem.name == name))
    if item:
        return item
    item = MenuItem(
        restaurant_id=restaurant.id,
        name=name,
        category=category,
        description=f"Popular {name} from {restaurant.name}",
        price_cents=price_cents,
        is_available=True,
    )
    db.add(item)
    return item


def seed() -> None:
    configure_database()
    create_schema()
    with session_scope() as db:
        owner = ensure_user(db, "owner@example.com", "Restaurant Owner", UserRole.RESTAURANT_OWNER)
        ensure_user(db, "customer@example.com", "Customer Demo", UserRole.CUSTOMER)
        ensure_user(db, "partner@example.com", "Delivery Partner", UserRole.DELIVERY_PARTNER)
        ensure_user(db, "admin@example.com", "Admin Demo", UserRole.ADMIN)

        restaurant = db.scalar(select(Restaurant).where(Restaurant.name == "Spice Hub"))
        if not restaurant:
            restaurant = Restaurant(
                owner_id=owner.id,
                name="Spice Hub",
                description="Fast Indian comfort food",
                cuisine="Indian",
                address="42 MG Road, Bengaluru",
                city="Bengaluru",
                delivery_fee_cents=2500,
                min_order_amount_cents=10000,
            )
            db.add(restaurant)
            db.flush()
        ensure_menu_item(db, restaurant, "Paneer Biryani", "BIRYANI", 12000)
        ensure_menu_item(db, restaurant, "Masala Dosa", "BREAKFAST", 8000)
        ensure_menu_item(db, restaurant, "Mango Lassi", "DRINKS", 4500)

    print("Seed complete. Demo password for all users: Password123")


if __name__ == "__main__":
    seed()
