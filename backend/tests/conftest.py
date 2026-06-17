from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("AUTO_CREATE_TABLES", "true")
os.environ.setdefault("JWT_SECRET", "test-secret-with-at-least-32-bytes!!")

from app.core.cache import cache
from app.core.config import reset_settings_cache
from app.core.database import drop_schema
from app.main import create_app


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    db_file = tmp_path / "test_food_delivery.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")
    monkeypatch.setenv("AUTO_CREATE_TABLES", "true")
    monkeypatch.setenv("JWT_SECRET", "test-secret-with-at-least-32-bytes!!")
    reset_settings_cache()
    cache.clear()
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
    drop_schema()
    cache.clear()


def register_user(client: TestClient, email: str, password: str = "Password123", role: str = "CUSTOMER", full_name: str = "Test User") -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": full_name, "role": role},
    )
    assert response.status_code == 201, response.text
    return response.json()


def auth_headers(token_response: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {token_response['access_token']}"}


def create_restaurant_and_menu(client: TestClient, owner_token: dict) -> tuple[dict, dict]:
    headers = auth_headers(owner_token)
    restaurant_response = client.post(
        "/api/v1/restaurants",
        headers=headers,
        json={
            "name": "Spice Hub",
            "description": "Fast Indian meals",
            "cuisine": "Indian",
            "address": "42 MG Road, Bengaluru",
            "city": "Bengaluru",
            "delivery_fee_cents": 2500,
            "min_order_amount_cents": 10000,
        },
    )
    assert restaurant_response.status_code == 201, restaurant_response.text
    restaurant = restaurant_response.json()
    menu_response = client.post(
        f"/api/v1/restaurants/{restaurant['id']}/menu-items",
        headers=headers,
        json={
            "name": "Paneer Biryani",
            "description": "Aromatic rice with paneer",
            "category": "BIRYANI",
            "price_cents": 12000,
            "is_available": True,
        },
    )
    assert menu_response.status_code == 201, menu_response.text
    return restaurant, menu_response.json()
