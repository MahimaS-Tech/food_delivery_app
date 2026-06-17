from fastapi.testclient import TestClient

from tests.conftest import auth_headers, create_restaurant_and_menu, register_user


def test_order_visibility_is_scoped_to_customer_and_owner(client: TestClient) -> None:
    owner = register_user(client, "scope-owner@example.com", role="RESTAURANT_OWNER")
    customer = register_user(client, "scope-customer@example.com", role="CUSTOMER")
    other_customer = register_user(client, "scope-other@example.com", role="CUSTOMER")
    _, menu_item = create_restaurant_and_menu(client, owner)
    client.post("/api/v1/cart/items", headers=auth_headers(customer), json={"menu_item_id": menu_item["id"], "quantity": 1})
    order = client.post(
        "/api/v1/orders",
        headers={**auth_headers(customer), "X-Idempotency-Key": "scope-key-001"},
        json={"delivery_address": "44 Church Street, Bengaluru", "payment_method": "CARD"},
    ).json()

    forbidden = client.get(f"/api/v1/orders/{order['id']}", headers=auth_headers(other_customer))
    assert forbidden.status_code == 403

    owner_view = client.get(f"/api/v1/orders/{order['id']}", headers=auth_headers(owner))
    assert owner_view.status_code == 200


def test_delivery_assignment_and_delivery_partner_view(client: TestClient) -> None:
    owner = register_user(client, "delivery-owner@example.com", role="RESTAURANT_OWNER")
    customer = register_user(client, "delivery-customer@example.com", role="CUSTOMER")
    partner = register_user(client, "delivery-partner@example.com", role="DELIVERY_PARTNER")
    _, menu_item = create_restaurant_and_menu(client, owner)
    client.post("/api/v1/cart/items", headers=auth_headers(customer), json={"menu_item_id": menu_item["id"], "quantity": 1})
    order = client.post(
        "/api/v1/orders",
        headers={**auth_headers(customer), "X-Idempotency-Key": "delivery-key-001"},
        json={"delivery_address": "99 Indiranagar, Bengaluru", "payment_method": "UPI"},
    ).json()

    assignment = client.post(
        f"/api/v1/orders/{order['id']}/assign-delivery",
        headers=auth_headers(owner),
        json={"partner_id": partner["user"]["id"]},
    )
    assert assignment.status_code == 200
    assert assignment.json()["delivery_partner_id"] == partner["user"]["id"]

    partner_orders = client.get("/api/v1/orders", headers=auth_headers(partner))
    assert partner_orders.status_code == 200
    assert len(partner_orders.json()) == 1
