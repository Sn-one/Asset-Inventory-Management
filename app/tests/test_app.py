import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from app.api.v1.routers.assets import reset_asset_store
from app.main import app


client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_assets() -> None:
    reset_asset_store()


from app.main import app

client = TestClient(app)


def test_health_check() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_asset_lifecycle_routes() -> None:
    created = client.post(
        "/api/v1/assets",
        json={"asset_tag": "AST-100", "serial_no": "S-1", "category": "Laptop", "location": "HQ"},
    )
    assert created.status_code == 201
    asset_id = created.json()["id"]
    assert created.json()["status"] == "in_stock"

    listing = client.get("/api/v1/assets")
    assert listing.status_code == 200
    assert len(listing.json()["items"]) == 1

    status_resp = client.post(f"/api/v1/assets/{asset_id}/status", json={"status": "assigned"})
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "assigned"


def test_reject_invalid_status_transition() -> None:
    created = client.post("/api/v1/assets", json={"asset_tag": "AST-200"})
    asset_id = created.json()["id"]
    client.post(f"/api/v1/assets/{asset_id}/status", json={"status": "disposed"})
    invalid = client.post(f"/api/v1/assets/{asset_id}/status", json={"status": "assigned"})
    assert invalid.status_code == 400
def test_list_assets() -> None:
    response = client.get("/api/v1/assets")
    assert response.status_code == 200
    assert response.json() == {"items": []}


def test_auth_login_and_me() -> None:
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "admin123"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    me_response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "admin@example.com"
