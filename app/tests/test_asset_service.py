import pytest

pytest.importorskip("pydantic")

from app.schemas.asset import AssetStatus
from app.services.asset_service import can_transition


def test_allows_valid_transition() -> None:
    assert can_transition(AssetStatus.IN_STOCK, AssetStatus.ASSIGNED)


def test_rejects_invalid_transition() -> None:
    assert not can_transition(AssetStatus.DISPOSED, AssetStatus.IN_STOCK)
