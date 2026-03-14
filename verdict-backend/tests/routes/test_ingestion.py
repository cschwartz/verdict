from collections.abc import Generator

import httpx
import pytest
import respx
from httpx import AsyncClient
from sqlmodel import Session, select

from app.deps import get_http_client
from app.main import app
from app.models.system import System


@pytest.fixture
def mock_http_client() -> Generator[None, None, None]:
    def _override() -> Generator[httpx.Client, None, None]:
        with httpx.Client() as client:
            yield client

    app.dependency_overrides[get_http_client] = _override
    yield
    app.dependency_overrides.pop(get_http_client, None)


ASSET_INDEX = [
    {"id": "SVC-001", "name": "Online Banking Portal"},
]
ASSET_DETAIL = {
    "SVC-001": {
        "id": "SVC-001",
        "name": "Online Banking Portal",
        "description": "Customer-facing online banking application",
        "tags": ["protection-level:high"],
    },
}
SYSTEM_INDEX = [
    {"id": "SYS-001", "primary_fqdn": "host.example.com"},
]
SYSTEM_DETAIL = {
    "SYS-001": {
        "id": "SYS-001",
        "primary_fqdn": "host.example.com",
        "asset_gold_source_ids": ["SVC-001"],
        "tags": ["env:production"],
    },
}


def _mock_all_services() -> None:
    respx.get("http://localhost:4010/assets").respond(200, json=ASSET_INDEX)
    for item_id, payload in ASSET_DETAIL.items():
        respx.get(f"http://localhost:4010/assets/{item_id}").respond(200, json=payload)
    respx.get("http://localhost:4011/systems").respond(200, json=SYSTEM_INDEX)
    for item_id, payload in SYSTEM_DETAIL.items():
        respx.get(f"http://localhost:4011/systems/{item_id}").respond(200, json=payload)


@respx.mock
async def test_full_ingest_endpoint(app_client: AsyncClient, db_session, mock_http_client):
    _mock_all_services()

    response = await app_client.post("/ingest")

    assert response.status_code == 200
    data = response.json()
    assert data["assets_ingested"] == 1
    assert data["systems_ingested"] == 1


def _mock_system_failure() -> None:
    respx.get("http://localhost:4010/assets").respond(200, json=ASSET_INDEX)
    for item_id, payload in ASSET_DETAIL.items():
        respx.get(f"http://localhost:4010/assets/{item_id}").respond(200, json=payload)
    respx.get("http://localhost:4011/systems").respond(200, json=SYSTEM_INDEX)
    # System detail references a nonexistent asset
    respx.get("http://localhost:4011/systems/SYS-001").respond(
        200,
        json={
            "id": "SYS-001",
            "primary_fqdn": "host.example.com",
            "asset_gold_source_ids": ["NONEXISTENT"],
            "tags": [],
        },
    )


@respx.mock
async def test_full_ingest_returns_502_on_system_failure(
    app_client: AsyncClient, db_session, mock_http_client
):
    _mock_system_failure()

    response = await app_client.post("/ingest")

    assert response.status_code == 502


@respx.mock
async def test_full_ingest_does_not_persist_on_system_failure(
    app_client: AsyncClient, db_session: Session, mock_http_client
):
    _mock_system_failure()

    await app_client.post("/ingest")

    systems = db_session.exec(select(System)).all()
    assert len(systems) == 0
