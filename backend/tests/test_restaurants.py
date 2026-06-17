from fastapi.testclient import TestClient

from tests.conftest import auth_headers, create_restaurant_and_menu, register_user


def test_customer_cannot_create_restaurant(client: TestClient) -> None:
    customer = register_user(client, "customer-role@example.com")
    response = client.post(
        "/api/v1/restaurants",
        headers=auth_headers(customer),
        json={
            "name": "Not Allowed",
            "cuisine": "Cafe",
            "address": "100 Main Street",
            "city": "Mumbai",
        },
    )
    assert response.status_code == 403


def test_owner_creates_restaurant_and_menu_search_works(client: TestClient) -> None:
    owner = register_user(client, "owner@example.com", role="RESTAURANT_OWNER", full_name="Owner")
    restaurant, menu_item = create_restaurant_and_menu(client, owner)

    search = client.get("/api/v1/restaurants", params={"city": "Bengaluru", "cuisine": "Indian"})
    assert search.status_code == 200
    assert len(search.json()) == 1
    assert search.json()[0]["id"] == restaurant["id"]

    menu = client.get(f"/api/v1/restaurants/{restaurant['id']}/menu")
    assert menu.status_code == 200
    assert menu.json()[0]["name"] == menu_item["name"]


def test_non_owner_cannot_update_someone_elses_restaurant(client: TestClient) -> None:
    owner = register_user(client, "owner-one@example.com", role="RESTAURANT_OWNER")
    other_owner = register_user(client, "owner-two@example.com", role="RESTAURANT_OWNER")
    restaurant, _ = create_restaurant_and_menu(client, owner)
    response = client.patch(
        f"/api/v1/restaurants/{restaurant['id']}",
        headers=auth_headers(other_owner),
        json={"status": "CLOSED"},
    )
    assert response.status_code == 403
