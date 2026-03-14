from httpx import AsyncClient

from tests.factories.asset import AssetFactory


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
