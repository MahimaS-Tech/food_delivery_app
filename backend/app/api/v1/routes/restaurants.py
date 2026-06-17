from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.restaurant import MenuItemCreate, MenuItemRead, MenuItemUpdate, RestaurantCreate, RestaurantRead, RestaurantUpdate, RestaurantWithMenu
from app.services.restaurant_service import (
    create_menu_item,
    create_restaurant,
    get_restaurant_or_404,
    get_restaurant_with_menu,
    list_menu_items,
    list_restaurants,
    update_menu_item,
    update_restaurant,
)

router = APIRouter(prefix="/restaurants", tags=["restaurants"])


@router.get("", response_model=list[RestaurantRead])
def search_restaurants(
    city: str | None = None,
    cuisine: str | None = None,
    q: str | None = None,
    open_only: bool = True,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[dict]:
    return list_restaurants(db, city=city, cuisine=cuisine, q=q, open_only=open_only, limit=limit, offset=offset)


@router.post("", response_model=RestaurantRead, status_code=status.HTTP_201_CREATED)
def create_restaurant_endpoint(
    payload: RestaurantCreate,
    db: Session = Depends(get_db),
    owner: User = Depends(require_roles(UserRole.RESTAURANT_OWNER, UserRole.ADMIN)),
):
    return create_restaurant(db, owner, payload)


@router.get("/{restaurant_id}", response_model=RestaurantRead)
def get_restaurant(restaurant_id: str, db: Session = Depends(get_db)):
    return get_restaurant_or_404(db, restaurant_id)


@router.patch("/{restaurant_id}", response_model=RestaurantRead)
def update_restaurant_endpoint(
    restaurant_id: str,
    payload: RestaurantUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return update_restaurant(db, user, restaurant_id, payload)


@router.get("/{restaurant_id}/menu", response_model=list[MenuItemRead])
def get_menu(
    restaurant_id: str,
    available_only: bool = True,
    db: Session = Depends(get_db),
):
    return list_menu_items(db, restaurant_id, available_only=available_only)


@router.get("/{restaurant_id}/with-menu", response_model=RestaurantWithMenu)
def get_restaurant_with_menu_endpoint(restaurant_id: str, db: Session = Depends(get_db)):
    return get_restaurant_with_menu(db, restaurant_id)


@router.post("/{restaurant_id}/menu-items", response_model=MenuItemRead, status_code=status.HTTP_201_CREATED)
def create_menu_item_endpoint(
    restaurant_id: str,
    payload: MenuItemCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.RESTAURANT_OWNER, UserRole.ADMIN)),
):
    return create_menu_item(db, user, restaurant_id, payload)


@router.patch("/{restaurant_id}/menu-items/{item_id}", response_model=MenuItemRead)
def update_menu_item_endpoint(
    restaurant_id: str,
    item_id: str,
    payload: MenuItemUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.RESTAURANT_OWNER, UserRole.ADMIN)),
):
    return update_menu_item(db, user, restaurant_id, item_id, payload)
