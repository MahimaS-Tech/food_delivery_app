from fastapi.testclient import TestClient

from tests.conftest import auth_headers, create_restaurant_and_menu, register_user


def test_cart_checkout_is_idempotent_and_clears_cart(client: TestClient) -> None:
    owner = register_user(client, "cart-owner@example.com", role="RESTAURANT_OWNER")
    customer = register_user(client, "cart-customer@example.com", role="CUSTOMER")
    restaurant, menu_item = create_restaurant_and_menu(client, owner)
    customer_headers = auth_headers(customer)

    cart = client.post(
        "/api/v1/cart/items",
        headers=customer_headers,
        json={"menu_item_id": menu_item["id"], "quantity": 2},
    )
    assert cart.status_code == 201, cart.text
    cart_body = cart.json()
    assert cart_body["subtotal_cents"] == 24000
    assert cart_body["delivery_fee_cents"] == 2500
    assert cart_body["total_cents"] == 27700  # 24000 + 5% tax + 2500 delivery.

    headers = {**customer_headers, "X-Idempotency-Key": "checkout-12345"}
    order = client.post(
        "/api/v1/orders",
        headers=headers,
        json={"delivery_address": "221B Baker Street, Bengaluru", "payment_method": "UPI"},
    )
    assert order.status_code == 201, order.text
    first_order = order.json()
    assert first_order["restaurant_id"] == restaurant["id"]
    assert first_order["status"] == "PLACED"
    assert len(first_order["items"]) == 1

    retry = client.post(
        "/api/v1/orders",
        headers=headers,
        json={"delivery_address": "221B Baker Street, Bengaluru", "payment_method": "UPI"},
    )
    assert retry.status_code == 201
    assert retry.json()["id"] == first_order["id"]

    empty_cart = client.get("/api/v1/cart", headers=customer_headers)
    assert empty_cart.status_code == 200
    assert empty_cart.json()["items"] == []


def test_order_status_transitions_and_invalid_transition(client: TestClient) -> None:
    owner = register_user(client, "status-owner@example.com", role="RESTAURANT_OWNER")
    customer = register_user(client, "status-customer@example.com", role="CUSTOMER")
    _, menu_item = create_restaurant_and_menu(client, owner)
    client.post("/api/v1/cart/items", headers=auth_headers(customer), json={"menu_item_id": menu_item["id"], "quantity": 1})
    order_response = client.post(
        "/api/v1/orders",
        headers={**auth_headers(customer), "X-Idempotency-Key": "status-key-001"},
        json={"delivery_address": "11 Residency Road, Bengaluru", "payment_method": "COD"},
    )
    order_id = order_response.json()["id"]

    accepted = client.patch(
        f"/api/v1/orders/{order_id}/status",
        headers=auth_headers(owner),
        json={"status": "ACCEPTED"},
    )
    assert accepted.status_code == 200
    assert accepted.json()["status"] == "ACCEPTED"

    invalid = client.patch(
        f"/api/v1/orders/{order_id}/status",
        headers=auth_headers(owner),
        json={"status": "DELIVERED"},
    )
    assert invalid.status_code == 409


def test_cart_rejects_multiple_restaurants(client: TestClient) -> None:
    owner1 = register_user(client, "multi-owner-1@example.com", role="RESTAURANT_OWNER")
    owner2 = register_user(client, "multi-owner-2@example.com", role="RESTAURANT_OWNER")
    customer = register_user(client, "multi-customer@example.com", role="CUSTOMER")
    _, item1 = create_restaurant_and_menu(client, owner1)
    _, item2 = create_restaurant_and_menu(client, owner2)
    headers = auth_headers(customer)
    assert client.post("/api/v1/cart/items", headers=headers, json={"menu_item_id": item1["id"], "quantity": 1}).status_code == 201
    response = client.post("/api/v1/cart/items", headers=headers, json={"menu_item_id": item2["id"], "quantity": 1})
    assert response.status_code == 409
