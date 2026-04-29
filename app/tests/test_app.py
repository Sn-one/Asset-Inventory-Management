import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_check() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_assets() -> None:
    response = client.get("/api/v1/assets")
    assert response.status_code == 200
    assert response.json() == {"items": []}
