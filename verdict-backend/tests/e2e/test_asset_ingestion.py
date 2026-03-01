"""E2E tests for asset ingestion flow.

These tests assume all services are running:
- PostgreSQL on localhost:5432
- Mock Asset Inventory on localhost:4010
- Verdict API on localhost:8000
"""

import httpx
import pytest

MOCK_INVENTORY_URL = "http://localhost:4010/assets"


def _ingest(client: httpx.Client) -> None:
    """Precondition helper: trigger ingestion. Raises on failure."""
    response = client.post("/assets/ingest")
    response.raise_for_status()


def _list_assets(client: httpx.Client) -> dict:
    """Precondition helper: fetch asset list. Raises on failure."""
    response = client.get("/assets/")
    response.raise_for_status()
    return response.json()


@pytest.mark.e2e
def test_ingest_and_list(http_client: httpx.Client):
    """Trigger ingestion, verify count matches mock data, then list assets."""
    # Arrange
    mock_response = httpx.get(MOCK_INVENTORY_URL)
    mock_response.raise_for_status()
    expected_count = len(mock_response.json())

    # Act
    response = http_client.post("/assets/ingest")

    # Assert
    assert response.status_code == 200
    assert response.json()["ingested"] == expected_count

    data = _list_assets(http_client)
    assert data["total"] == expected_count
    assert len(data["assets"]) == expected_count


@pytest.mark.e2e
def test_get_asset_by_id(http_client: httpx.Client):
    """Retrieve a specific asset by its database ID."""
    # Arrange
    _ingest(http_client)
    asset_id = _list_assets(http_client)["assets"][0]["id"]

    # Act
    response = http_client.get(f"/assets/{asset_id}")

    # Assert
    assert response.status_code == 200
    asset = response.json()
    assert asset["id"] == asset_id
    assert "name" in asset
    assert "description" in asset


@pytest.mark.e2e
def test_get_asset_by_gold_source(http_client: httpx.Client):
    """Retrieve an asset by its gold source type and ID."""
    # Arrange
    _ingest(http_client)
    first_asset = _list_assets(http_client)["assets"][0]
    source_type = first_asset["gold_source_type"]
    source_id = first_asset["gold_source_id"]

    # Act
    response = http_client.get(f"/assets/by-gold-source/{source_type}/{source_id}")

    # Assert
    assert response.status_code == 200
    retrieved = response.json()
    assert retrieved["gold_source_id"] == source_id
    assert retrieved["name"] == first_asset["name"]


@pytest.mark.e2e
def test_reingest_no_duplicates(http_client: httpx.Client):
    """Re-ingesting should upsert, not duplicate."""
    # Arrange
    _ingest(http_client)
    total_after_first = _list_assets(http_client)["total"]

    # Act
    response = http_client.post("/assets/ingest")

    # Assert
    assert response.status_code == 200
    assert response.json()["ingested"] == total_after_first
    assert _list_assets(http_client)["total"] == total_after_first


@pytest.mark.e2e
def test_asset_not_found(http_client: httpx.Client):
    response = http_client.get("/assets/999999")
    assert response.status_code == 404


@pytest.mark.e2e
def test_gold_source_not_found(http_client: httpx.Client):
    response = http_client.get("/assets/by-gold-source/asset-inventory/nonexistent")
    assert response.status_code == 404
