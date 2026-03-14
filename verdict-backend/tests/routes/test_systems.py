import sqlalchemy as sa
from httpx import AsyncClient

from app.models.system import asset_system
from tests.factories.asset import AssetFactory
from tests.factories.system import SystemFactory


async def test_list_systems(app_client: AsyncClient, db_session):
    SystemFactory.create()
    SystemFactory.create()

    response = await app_client.get("/systems/")

    assert response.status_code == 200
    data = response.json()
    assert len(data["systems"]) == 2
    assert data["total"] == 2


async def test_list_systems_pagination(app_client: AsyncClient, db_session):
    SystemFactory.create()
    SystemFactory.create()
    SystemFactory.create()

    response = await app_client.get("/systems/?offset=1&limit=1")

    assert response.status_code == 200
    data = response.json()
    assert len(data["systems"]) == 1
    assert data["total"] == 3


async def test_get_system_by_id(app_client: AsyncClient, db_session):
    system = SystemFactory.create()

    response = await app_client.get(f"/systems/{system.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["primary_fqdn"] == system.primary_fqdn
    assert data["gold_source_id"] == system.gold_source_id


async def test_get_system_not_found(app_client: AsyncClient, db_session):
    response = await app_client.get("/systems/99999")

    assert response.status_code == 404


async def test_get_system_by_gold_source(app_client: AsyncClient, db_session):
    system = SystemFactory.create()

    response = await app_client.get(
        f"/systems/by-gold-source/{system.gold_source_type}/{system.gold_source_id}"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["primary_fqdn"] == system.primary_fqdn


async def test_get_system_by_gold_source_not_found(app_client: AsyncClient, db_session):
    response = await app_client.get("/systems/by-gold-source/cmdb/nonexistent")

    assert response.status_code == 404


async def test_get_system_includes_asset_ids(app_client: AsyncClient, db_session):
    asset = AssetFactory.create()
    system = SystemFactory.create()
    db_session.execute(sa.insert(asset_system).values(asset_id=asset.id, system_id=system.id))
    db_session.flush()

    response = await app_client.get(f"/systems/{system.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["asset_ids"] == [asset.id]
