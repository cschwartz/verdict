from collections.abc import Generator

import httpx
import respx
from httpx import AsyncClient

from app.deps import get_http_client
from app.main import app
from tests.factories.asset import AssetFactory

INDEX_PAYLOAD = [
    {"id": "SVC-001", "name": "Online Banking Portal"},
    {"id": "SVC-002", "name": "Customer CRM"},
]

DETAIL_PAYLOADS = {
    "SVC-001": {
        "id": "SVC-001",
        "name": "Online Banking Portal",
        "description": "Customer-facing online banking application",
        "tags": ["protection-level:high", "business-unit:retail-banking"],
    },
    "SVC-002": {
        "id": "SVC-002",
        "name": "Customer CRM",
        "description": "Internal CRM system for customer relationships",
        "tags": ["protection-level:medium", "business-unit:customer-service"],
    },
}


async def test_list_assets(app_client: AsyncClient, db_session):
    AssetFactory.create()
    AssetFactory.create()

    response = await app_client.get("/assets/")

    assert response.status_code == 200
    data = response.json()
    assert len(data["assets"]) == 2
    assert data["total"] == 2


async def test_list_assets_pagination(app_client: AsyncClient, db_session):
    AssetFactory.create()
    AssetFactory.create()
    AssetFactory.create()

    response = await app_client.get("/assets/?offset=1&limit=1")

    assert response.status_code == 200
    data = response.json()
    assert len(data["assets"]) == 1
    assert data["total"] == 3


async def test_get_asset_by_id(app_client: AsyncClient, db_session):
    asset = AssetFactory.create()

    response = await app_client.get(f"/assets/{asset.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == asset.name
    assert data["gold_source_id"] == asset.gold_source_id


async def test_get_asset_not_found(app_client: AsyncClient, db_session):
    response = await app_client.get("/assets/99999")

    assert response.status_code == 404


async def test_get_asset_by_gold_source(app_client: AsyncClient, db_session):
    asset = AssetFactory.create()

    response = await app_client.get(
        f"/assets/by-gold-source/{asset.gold_source_type}/{asset.gold_source_id}"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == asset.name


async def test_get_asset_by_gold_source_not_found(app_client: AsyncClient, db_session):
    response = await app_client.get("/assets/by-gold-source/asset-inventory/nonexistent")

    assert response.status_code == 404


@respx.mock
async def test_ingest_endpoint(app_client: AsyncClient, db_session):
    respx.get("http://localhost:4010/assets").respond(200, json=INDEX_PAYLOAD)
    for item_id, payload in DETAIL_PAYLOADS.items():
        respx.get(f"http://localhost:4010/assets/{item_id}").respond(200, json=payload)

    def _mock_http_client() -> Generator[httpx.Client, None, None]:
        with httpx.Client() as client:
            yield client

    app.dependency_overrides[get_http_client] = _mock_http_client

    response = await app_client.post("/assets/ingest")

    assert response.status_code == 200
    assert response.json()["ingested"] == 2

    app.dependency_overrides.pop(get_http_client, None)
