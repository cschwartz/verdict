import httpx
import respx
from sqlmodel import select

from app.errors import FetchError, ValidationError
from app.models.asset import Asset
from app.models.gold_source import GoldSourceType
from app.result import Err, Ok
from app.schemas.external.asset_inventory import AssetDetail
from app.services.asset_ingestion import fetch_detail, fetch_index, ingest_assets, to_asset

FAKE_URL = "http://mock-inventory/assets"

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


def _mock_index_and_details() -> None:
    respx.get(FAKE_URL).respond(200, json=INDEX_PAYLOAD)
    for item_id, payload in DETAIL_PAYLOADS.items():
        respx.get(f"{FAKE_URL}/{item_id}").respond(200, json=payload)


# --- fetch_index tests ---


@respx.mock
def test_fetch_index_success():
    respx.get(FAKE_URL).respond(200, json=INDEX_PAYLOAD)

    with httpx.Client() as client:
        result = fetch_index(client, FAKE_URL)

    assert isinstance(result, Ok)
    assert len(result.value) == 2
    assert result.value[0].id == "SVC-001"
    assert result.value[0].name == "Online Banking Portal"


@respx.mock
def test_fetch_index_invalid_response():
    respx.get(FAKE_URL).respond(200, json=[{"name": "Missing id field"}])

    with httpx.Client() as client:
        result = fetch_index(client, FAKE_URL)

    assert isinstance(result, Err)
    assert isinstance(result.value, ValidationError)


@respx.mock
def test_fetch_index_fetch_error():
    respx.get(FAKE_URL).respond(500)

    with httpx.Client() as client:
        result = fetch_index(client, FAKE_URL)

    assert isinstance(result, Err)
    assert isinstance(result.value, FetchError)


# --- fetch_detail tests ---


@respx.mock
def test_fetch_detail_success():
    respx.get(f"{FAKE_URL}/SVC-001").respond(200, json=DETAIL_PAYLOADS["SVC-001"])

    with httpx.Client() as client:
        result = fetch_detail(client, FAKE_URL, "SVC-001")

    assert isinstance(result, Ok)
    assert result.value.id == "SVC-001"
    assert result.value.description == "Customer-facing online banking application"
    assert result.value.tags == ["protection-level:high", "business-unit:retail-banking"]


@respx.mock
def test_fetch_detail_not_found():
    respx.get(f"{FAKE_URL}/nonexistent").respond(404)

    with httpx.Client() as client:
        result = fetch_detail(client, FAKE_URL, "nonexistent")

    assert isinstance(result, Err)
    assert isinstance(result.value, FetchError)


@respx.mock
def test_fetch_detail_invalid_response():
    respx.get(f"{FAKE_URL}/SVC-001").respond(200, json={"id": "SVC-001"})

    with httpx.Client() as client:
        result = fetch_detail(client, FAKE_URL, "SVC-001")

    assert isinstance(result, Err)
    assert isinstance(result.value, ValidationError)


# --- to_asset tests ---


def test_to_asset():
    detail = AssetDetail(
        id="SVC-001",
        name="Online Banking Portal",
        description="Customer-facing online banking application",
        tags=["protection-level:high"],
    )
    asset = to_asset(detail)

    assert asset.name == "Online Banking Portal"
    assert asset.description == "Customer-facing online banking application"
    assert asset.tags == ["protection-level:high"]
    assert asset.gold_source_id == "SVC-001"
    assert asset.gold_source_type == GoldSourceType.ASSET_INVENTORY


# --- ingest_assets integration tests ---


@respx.mock
def test_ingest_valid_response(db_session):
    _mock_index_and_details()

    with httpx.Client() as client:
        result = ingest_assets(db_session, client, FAKE_URL)

    assert isinstance(result, Ok)
    assert len(result.value) == 2

    assets = list(db_session.exec(select(Asset)).all())
    assert len(assets) == 2
    assert assets[0].name == "Online Banking Portal"
    assert assets[0].gold_source_id == "SVC-001"
    assert assets[0].tags == ["protection-level:high", "business-unit:retail-banking"]


@respx.mock
def test_ingest_invalid_index_persists_nothing(db_session):
    respx.get(FAKE_URL).respond(200, json=[{"name": "Missing id field"}])

    with httpx.Client() as client:
        result = ingest_assets(db_session, client, FAKE_URL)

    assert isinstance(result, Err)
    assert isinstance(result.value, ValidationError)

    assets = list(db_session.exec(select(Asset)).all())
    assert len(assets) == 0


@respx.mock
def test_reingest_upserts_without_duplicates(db_session):
    _mock_index_and_details()

    with httpx.Client() as client:
        result = ingest_assets(db_session, client, FAKE_URL)
    assert isinstance(result, Ok)
    db_session.flush()

    updated_details = {k: {**v, "name": f"{v['name']} v2"} for k, v in DETAIL_PAYLOADS.items()}
    respx.get(FAKE_URL).respond(200, json=INDEX_PAYLOAD)
    for item_id, payload in updated_details.items():
        respx.get(f"{FAKE_URL}/{item_id}").respond(200, json=payload)

    with httpx.Client() as client:
        result = ingest_assets(db_session, client, FAKE_URL)

    assert isinstance(result, Ok)

    assets = list(db_session.exec(select(Asset)).all())
    assert len(assets) == 2
    names = sorted(a.name for a in assets)
    assert names == ["Customer CRM v2", "Online Banking Portal v2"]


@respx.mock
def test_ingest_fetch_error(db_session):
    respx.get(FAKE_URL).respond(500)

    with httpx.Client() as client:
        result = ingest_assets(db_session, client, FAKE_URL)

    assert isinstance(result, Err)
    assert isinstance(result.value, FetchError)


@respx.mock
def test_ingest_detail_fetch_error_persists_nothing(db_session):
    respx.get(FAKE_URL).respond(200, json=INDEX_PAYLOAD)
    respx.get(f"{FAKE_URL}/SVC-001").respond(500)

    with httpx.Client() as client:
        result = ingest_assets(db_session, client, FAKE_URL)

    assert isinstance(result, Err)
    assert isinstance(result.value, FetchError)

    assets = list(db_session.exec(select(Asset)).all())
    assert len(assets) == 0
