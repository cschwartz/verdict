import httpx
import respx
import sqlalchemy as sa
from sqlmodel import select

from app.errors import FetchError, RemoteValidationError
from app.models.gold_source import GoldSourceType
from app.models.system import System, SystemCreate, asset_system
from app.result import Err, Ok
from app.schemas.external.cmdb import SystemDetail
from app.services.cmdb_ingestion import (
    fetch_detail,
    fetch_index,
    ingest_systems,
    to_system,
)
from tests.factories.asset import AssetFactory

FAKE_URL = "http://mock-cmdb/systems"

INDEX_PAYLOAD = [
    {"id": "SYS-001", "primary_fqdn": "banking-web-01.prod.example.com"},
    {"id": "SYS-002", "primary_fqdn": "shared-db-01.prod.example.com"},
]

DETAIL_PAYLOADS = {
    "SYS-001": {
        "id": "SYS-001",
        "primary_fqdn": "banking-web-01.prod.example.com",
        "asset_gold_source_ids": ["SVC-001"],
        "tags": ["env:production", "tier:frontend"],
    },
    "SYS-002": {
        "id": "SYS-002",
        "primary_fqdn": "shared-db-01.prod.example.com",
        "asset_gold_source_ids": ["SVC-001", "SVC-002"],
        "tags": ["env:production", "tier:data"],
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
    assert result.value[0].id == "SYS-001"


@respx.mock
def test_fetch_index_invalid_response():
    respx.get(FAKE_URL).respond(200, json=[{"name": "Missing fields"}])

    with httpx.Client() as client:
        result = fetch_index(client, FAKE_URL)

    assert isinstance(result, Err)
    assert isinstance(result.value, RemoteValidationError)


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
    respx.get(f"{FAKE_URL}/SYS-001").respond(200, json=DETAIL_PAYLOADS["SYS-001"])

    with httpx.Client() as client:
        result = fetch_detail(client, FAKE_URL, "SYS-001")

    assert isinstance(result, Ok)
    assert result.value.id == "SYS-001"
    assert result.value.primary_fqdn == "banking-web-01.prod.example.com"
    assert result.value.asset_gold_source_ids == ["SVC-001"]


@respx.mock
def test_fetch_detail_not_found():
    respx.get(f"{FAKE_URL}/nonexistent").respond(404)

    with httpx.Client() as client:
        result = fetch_detail(client, FAKE_URL, "nonexistent")

    assert isinstance(result, Err)
    assert isinstance(result.value, FetchError)


@respx.mock
def test_fetch_detail_invalid_response():
    respx.get(f"{FAKE_URL}/SYS-001").respond(200, json={"id": "SYS-001"})

    with httpx.Client() as client:
        result = fetch_detail(client, FAKE_URL, "SYS-001")

    assert isinstance(result, Err)
    assert isinstance(result.value, RemoteValidationError)


# --- to_system tests ---


def test_to_system():
    detail = SystemDetail(
        id="SYS-001",
        primary_fqdn="banking-web-01.prod.example.com",
        asset_gold_source_ids=["SVC-001"],
        tags=["env:production"],
    )
    system = to_system(detail)

    assert isinstance(system, SystemCreate)
    assert system.primary_fqdn == "banking-web-01.prod.example.com"
    assert system.gold_source_id == "SYS-001"
    assert system.gold_source_type == GoldSourceType.CMDB


# --- ingest_systems integration tests ---


@respx.mock
def test_ingest_valid_response(db_session):
    AssetFactory.create(gold_source_id="SVC-001")
    AssetFactory.create(gold_source_id="SVC-002")
    _mock_index_and_details()

    with httpx.Client() as client:
        result = ingest_systems(db_session, client, FAKE_URL)

    assert isinstance(result, Ok)
    assert len(result.value) == 2

    systems = list(db_session.exec(select(System).order_by(System.gold_source_id)).all())
    assert len(systems) == 2
    assert systems[0].primary_fqdn == "banking-web-01.prod.example.com"


@respx.mock
def test_ingest_system_without_asset_links(db_session):
    index = [{"id": "SYS-003", "primary_fqdn": "monitoring-01.infra.example.com"}]
    detail = {
        "id": "SYS-003",
        "primary_fqdn": "monitoring-01.infra.example.com",
        "asset_gold_source_ids": [],
        "tags": ["env:production"],
    }
    respx.get(FAKE_URL).respond(200, json=index)
    respx.get(f"{FAKE_URL}/SYS-003").respond(200, json=detail)

    with httpx.Client() as client:
        result = ingest_systems(db_session, client, FAKE_URL)

    assert isinstance(result, Ok)
    assert len(result.value) == 1


@respx.mock
def test_ingest_unresolvable_asset_rejects_all(db_session):
    index = [{"id": "SYS-001", "primary_fqdn": "host.example.com"}]
    detail = {
        "id": "SYS-001",
        "primary_fqdn": "host.example.com",
        "asset_gold_source_ids": ["NONEXISTENT"],
        "tags": [],
    }
    respx.get(FAKE_URL).respond(200, json=index)
    respx.get(f"{FAKE_URL}/SYS-001").respond(200, json=detail)

    with httpx.Client() as client:
        result = ingest_systems(db_session, client, FAKE_URL)

    assert isinstance(result, Err)
    assert isinstance(result.value, RemoteValidationError)

    systems = list(db_session.exec(select(System)).all())
    assert len(systems) == 0


@respx.mock
def test_reingest_upserts_without_duplicates(db_session):
    AssetFactory.create(gold_source_id="SVC-001")
    AssetFactory.create(gold_source_id="SVC-002")
    _mock_index_and_details()

    with httpx.Client() as client:
        result = ingest_systems(db_session, client, FAKE_URL)
    assert isinstance(result, Ok)
    db_session.flush()

    updated_details = {
        k: {**v, "primary_fqdn": f"updated-{v['primary_fqdn']}"} for k, v in DETAIL_PAYLOADS.items()
    }
    respx.get(FAKE_URL).respond(200, json=INDEX_PAYLOAD)
    for item_id, payload in updated_details.items():
        respx.get(f"{FAKE_URL}/{item_id}").respond(200, json=payload)

    with httpx.Client() as client:
        result = ingest_systems(db_session, client, FAKE_URL)

    assert isinstance(result, Ok)

    systems = list(db_session.exec(select(System)).all())
    assert len(systems) == 2
    fqdns = sorted(s.primary_fqdn for s in systems)
    assert all(f.startswith("updated-") for f in fqdns)


@respx.mock
def test_reingest_updates_asset_links(db_session):
    asset1 = AssetFactory.create(gold_source_id="SVC-001")
    asset2 = AssetFactory.create(gold_source_id="SVC-002")

    index = [{"id": "SYS-001", "primary_fqdn": "host.example.com"}]
    detail_v1 = {
        "id": "SYS-001",
        "primary_fqdn": "host.example.com",
        "asset_gold_source_ids": ["SVC-001"],
        "tags": [],
    }
    respx.get(FAKE_URL).respond(200, json=index)
    respx.get(f"{FAKE_URL}/SYS-001").respond(200, json=detail_v1)

    with httpx.Client() as client:
        result = ingest_systems(db_session, client, FAKE_URL)
    assert isinstance(result, Ok)
    db_session.flush()

    system = db_session.exec(select(System)).first()
    assert system is not None
    link_ids = {
        row.asset_id
        for row in db_session.execute(
            sa.select(asset_system.c.asset_id).where(asset_system.c.system_id == system.id)
        ).all()
    }
    assert link_ids == {asset1.id}

    detail_v2 = {
        "id": "SYS-001",
        "primary_fqdn": "host.example.com",
        "asset_gold_source_ids": ["SVC-002"],
        "tags": [],
    }
    respx.get(FAKE_URL).respond(200, json=index)
    respx.get(f"{FAKE_URL}/SYS-001").respond(200, json=detail_v2)

    with httpx.Client() as client:
        result = ingest_systems(db_session, client, FAKE_URL)
    assert isinstance(result, Ok)
    db_session.flush()

    link_ids = {
        row.asset_id
        for row in db_session.execute(
            sa.select(asset_system.c.asset_id).where(asset_system.c.system_id == system.id)
        ).all()
    }
    assert link_ids == {asset2.id}


@respx.mock
def test_ingest_fetch_error(db_session):
    respx.get(FAKE_URL).respond(500)

    with httpx.Client() as client:
        result = ingest_systems(db_session, client, FAKE_URL)

    assert isinstance(result, Err)
    assert isinstance(result.value, FetchError)


@respx.mock
def test_ingest_detail_fetch_error_persists_nothing(db_session):
    respx.get(FAKE_URL).respond(200, json=INDEX_PAYLOAD)
    respx.get(f"{FAKE_URL}/SYS-001").respond(500)

    with httpx.Client() as client:
        result = ingest_systems(db_session, client, FAKE_URL)

    assert isinstance(result, Err)
    assert isinstance(result.value, FetchError)

    systems = list(db_session.exec(select(System)).all())
    assert len(systems) == 0
