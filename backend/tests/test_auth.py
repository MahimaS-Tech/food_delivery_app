from fastapi.testclient import TestClient

from tests.conftest import auth_headers, register_user


def test_register_login_and_me(client: TestClient) -> None:
    created = register_user(client, "customer@example.com", full_name="Customer One")
    assert created["user"]["email"] == "customer@example.com"
    assert created["token_type"] == "bearer"

    me = client.get("/api/v1/auth/me", headers=auth_headers(created))
    assert me.status_code == 200
    assert me.json()["full_name"] == "Customer One"

    login = client.post("/api/v1/auth/login", json={"email": "customer@example.com", "password": "Password123"})
    assert login.status_code == 200
    assert login.json()["user"]["role"] == "CUSTOMER"


def test_duplicate_email_and_wrong_password(client: TestClient) -> None:
    register_user(client, "duplicate@example.com")
    duplicate = client.post(
        "/api/v1/auth/register",
        json={"email": "duplicate@example.com", "password": "Password123", "full_name": "Again", "role": "CUSTOMER"},
    )
    assert duplicate.status_code == 409

    wrong = client.post("/api/v1/auth/login", json={"email": "duplicate@example.com", "password": "wrong"})
    assert wrong.status_code == 401
