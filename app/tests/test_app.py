import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

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
    assert created.json()["status"] == "in_stock"

    listing = client.get("/api/v1/assets")
    assert listing.status_code == 200
    assert len(listing.json()["items"]) >= 1

    status_resp = client.post("/api/v1/assets/1/status", json={"status": "assigned"})
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "assigned"


def test_reject_invalid_status_transition() -> None:
    client.post("/api/v1/assets", json={"asset_tag": "AST-200"})
    client.post("/api/v1/assets/2/status", json={"status": "disposed"})
    invalid = client.post("/api/v1/assets/2/status", json={"status": "assigned"})
    assert invalid.status_code == 400
