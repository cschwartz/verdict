from urllib.parse import quote

import httpx
from pydantic import TypeAdapter
from sqlalchemy.exc import OperationalError
from sqlmodel import Session

from app.errors import DBError, FetchError, IngestionError, RemoteValidationError, db_error_from
from app.http import fetch_json
from app.models.asset import Asset, AssetCreate, AssetPublic
from app.models.gold_source import GoldSourceType
from app.queries import upsert_by_gold_source
from app.result import Err, Ok, Result
from app.schemas.external.asset_inventory import AssetDetail, AssetIndexItem

_index_adapter = TypeAdapter(list[AssetIndexItem])
_detail_adapter = TypeAdapter(AssetDetail)

type SourceError = FetchError | RemoteValidationError


def fetch_index(
    client: httpx.Client,
    url: str,
) -> Result[list[AssetIndexItem], SourceError]:
    return fetch_json(client, url, _index_adapter)


def fetch_detail(
    client: httpx.Client,
    url: str,
    item_id: str,
) -> Result[AssetDetail, SourceError]:
    return fetch_json(client, f"{url}/{quote(item_id, safe='')}", _detail_adapter)


def to_asset(detail: AssetDetail) -> AssetCreate:
    return AssetCreate(
        name=detail.name,
        description=detail.description,
        tags=detail.tags,
        gold_source_id=detail.id,
        gold_source_type=GoldSourceType.ASSET_INVENTORY,
    )


def ingest_assets(
    session: Session,
    client: httpx.Client,
    url: str,
) -> Result[list[AssetPublic], IngestionError]:
    index_result = fetch_index(client, url)
    if isinstance(index_result, Err):
        return Err(index_result.value)

    assets: list[AssetPublic] = []
    for index_item in index_result.value:
        detail_result = fetch_detail(client, url, index_item.id)
        if isinstance(detail_result, Err):
            return Err(detail_result.value)

        asset_create = to_asset(detail_result.value)
        upsert_result = _upsert_asset(session, asset_create)
        if isinstance(upsert_result, Err):
            return Err(upsert_result.value)
        assets.append(upsert_result.value)

    try:
        session.flush()
    except OperationalError as e:
        return Err(db_error_from(e))
    return Ok(assets)


def _upsert_asset(
    session: Session,
    asset_create: AssetCreate,
) -> Result[AssetPublic, DBError]:
    def on_existing(existing: Asset) -> None:
        existing.name = asset_create.name
        existing.description = asset_create.description
        existing.tags = asset_create.tags

    def make_new() -> Asset:
        return Asset.model_validate(asset_create, from_attributes=True)

    return upsert_by_gold_source(
        session,
        Asset,
        asset_create.gold_source_type,
        asset_create.gold_source_id,
        public_class=AssetPublic,
        on_existing=on_existing,
        make_new=make_new,
    )
