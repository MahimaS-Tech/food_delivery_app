from fastapi.testclient import TestClient


def test_health_endpoints(client: TestClient) -> None:
    assert client.get("/api/v1/health/live").json() == {"status": "alive"}
    ready = client.get("/api/v1/health/ready")
    assert ready.status_code == 200
    assert ready.json() == {"status": "ready"}
