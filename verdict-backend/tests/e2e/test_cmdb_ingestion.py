"""E2E tests for CMDB ingestion flow.

These tests assume all services are running:
- PostgreSQL on localhost:5432
- Mock Asset Inventory on localhost:4010
- Mock CMDB on localhost:4011
- Verdict API on localhost:8000
"""

import httpx
import pytest

MOCK_CMDB_URL = "http://localhost:4011/systems"


def _ingest(client: httpx.Client) -> dict:
    response = client.post("/ingest")
    response.raise_for_status()
    return response.json()


def _list_systems(client: httpx.Client) -> dict:
    response = client.get("/systems/")
    response.raise_for_status()
    return response.json()


@pytest.mark.e2e
def test_ingest_and_list(http_client: httpx.Client):
    mock_response = httpx.get(MOCK_CMDB_URL)
    mock_response.raise_for_status()
    expected_system_count = len(mock_response.json())

    result = _ingest(http_client)

    assert result["systems_ingested"] == expected_system_count

    data = _list_systems(http_client)
    assert data["total"] == expected_system_count


@pytest.mark.e2e
def test_get_system_by_id(http_client: httpx.Client):
    _ingest(http_client)
    system_id = _list_systems(http_client)["systems"][0]["id"]

    response = http_client.get(f"/systems/{system_id}")

    assert response.status_code == 200
    system = response.json()
    assert system["id"] == system_id
    assert "primary_fqdn" in system


@pytest.mark.e2e
def test_get_system_by_gold_source(http_client: httpx.Client):
    _ingest(http_client)
    first = _list_systems(http_client)["systems"][0]

    response = http_client.get(
        f"/systems/by-gold-source/{first['gold_source_type']}/{first['gold_source_id']}"
    )

    assert response.status_code == 200
    assert response.json()["gold_source_id"] == first["gold_source_id"]


@pytest.mark.e2e
def test_system_includes_asset_ids(http_client: httpx.Client):
    _ingest(http_client)
    systems = _list_systems(http_client)["systems"]
    system_with_assets = next(s for s in systems if s["asset_ids"])

    assert len(system_with_assets["asset_ids"]) > 0


@pytest.mark.e2e
def test_system_without_assets(http_client: httpx.Client):
    _ingest(http_client)
    systems = _list_systems(http_client)["systems"]
    system_no_assets = next(s for s in systems if not s["asset_ids"])

    assert system_no_assets["asset_ids"] == []


@pytest.mark.e2e
def test_reingest_no_duplicates(http_client: httpx.Client):
    _ingest(http_client)
    total_after_first = _list_systems(http_client)["total"]

    _ingest(http_client)

    assert _list_systems(http_client)["total"] == total_after_first


@pytest.mark.e2e
def test_system_not_found(http_client: httpx.Client):
    response = http_client.get("/systems/999999")
    assert response.status_code == 404


@pytest.mark.e2e
def test_gold_source_not_found(http_client: httpx.Client):
    response = http_client.get("/systems/by-gold-source/cmdb/nonexistent")
    assert response.status_code == 404


@pytest.mark.e2e
def test_full_ingest_endpoint(http_client: httpx.Client):
    result = _ingest(http_client)

    assert result["assets_ingested"] > 0
    assert result["systems_ingested"] > 0
