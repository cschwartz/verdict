"""E2E tests for asset ingestion flow.

These tests assume all services are running:
- PostgreSQL on localhost:5432
- Mock Asset Inventory on localhost:4010
- Mock CMDB on localhost:4011
- Verdict API on localhost:8000
"""

import httpx
import pytest

MOCK_INVENTORY_URL = "http://localhost:4010/assets"


def _ingest(client: httpx.Client) -> None:
    response = client.post("/ingest")
    response.raise_for_status()


def _list_assets(client: httpx.Client) -> dict:
    response = client.get("/assets/")
    response.raise_for_status()
    return response.json()


@pytest.mark.e2e
def test_ingest_and_list(http_client: httpx.Client):
    mock_response = httpx.get(MOCK_INVENTORY_URL)
    mock_response.raise_for_status()
    expected_count = len(mock_response.json())

    response = http_client.post("/ingest")

    assert response.status_code == 200
    assert response.json()["assets_ingested"] == expected_count

    data = _list_assets(http_client)
    assert data["total"] == expected_count
    assert len(data["assets"]) == expected_count


@pytest.mark.e2e
def test_get_asset_by_id(http_client: httpx.Client):
    _ingest(http_client)
    asset_id = _list_assets(http_client)["assets"][0]["id"]

    response = http_client.get(f"/assets/{asset_id}")

    assert response.status_code == 200
    asset = response.json()
    assert asset["id"] == asset_id
    assert "name" in asset
    assert "description" in asset


@pytest.mark.e2e
def test_get_asset_by_gold_source(http_client: httpx.Client):
    _ingest(http_client)
    first_asset = _list_assets(http_client)["assets"][0]
    source_type = first_asset["gold_source_type"]
    source_id = first_asset["gold_source_id"]

    response = http_client.get(f"/assets/by-gold-source/{source_type}/{source_id}")

    assert response.status_code == 200
    retrieved = response.json()
    assert retrieved["gold_source_id"] == source_id
    assert retrieved["name"] == first_asset["name"]


@pytest.mark.e2e
def test_reingest_no_duplicates(http_client: httpx.Client):
    _ingest(http_client)
    total_after_first = _list_assets(http_client)["total"]

    response = http_client.post("/ingest")

    assert response.status_code == 200
    assert response.json()["assets_ingested"] == total_after_first
    assert _list_assets(http_client)["total"] == total_after_first


@pytest.mark.e2e
def test_asset_not_found(http_client: httpx.Client):
    response = http_client.get("/assets/999999")
    assert response.status_code == 404


@pytest.mark.e2e
def test_gold_source_not_found(http_client: httpx.Client):
    response = http_client.get("/assets/by-gold-source/asset-inventory/nonexistent")
    assert response.status_code == 404
