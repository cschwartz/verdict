import logging
from urllib.parse import quote

import httpx
from pydantic import TypeAdapter
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.exc import OperationalError
from sqlmodel import Session

from app.errors import DBError, FetchError, IngestionError, ValidationError, db_error_from
from app.models.asset import Asset, AssetCreate, AssetPublic
from app.models.gold_source import GoldSourceMixin, GoldSourceType
from app.result import Err, Ok, Result, Some
from app.schemas.external.asset_inventory import AssetDetail, AssetIndexItem

logger = logging.getLogger(__name__)

_index_adapter = TypeAdapter(list[AssetIndexItem])
_detail_adapter = TypeAdapter(AssetDetail)

type SourceError = FetchError | ValidationError


def fetch_index(
    client: httpx.Client,
    url: str,
) -> Result[list[AssetIndexItem], SourceError]:
    try:
        response = client.get(url)
        response.raise_for_status()
    except httpx.HTTPError as e:
        return Err(FetchError(url=url, raw=str(e)))

    try:
        items = _index_adapter.validate_json(response.content)
    except PydanticValidationError as e:
        logger.error("Schema mismatch from asset inventory index: %s", e)
        return Err(ValidationError(raw=str(e)))

    return Ok(items)


def fetch_detail(
    client: httpx.Client,
    url: str,
    item_id: str,
) -> Result[AssetDetail, SourceError]:
    detail_url = f"{url}/{quote(item_id, safe='')}"
    try:
        response = client.get(detail_url)
        response.raise_for_status()
    except httpx.HTTPError as e:
        return Err(FetchError(url=detail_url, raw=str(e)))

    try:
        detail = _detail_adapter.validate_json(response.content)
    except PydanticValidationError as e:
        logger.error("Schema mismatch from asset inventory detail %s: %s", item_id, e)
        return Err(ValidationError(raw=str(e)))

    return Ok(detail)


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
    result = GoldSourceMixin.get_by_gold_source(
        session,
        Asset,
        asset_create.gold_source_type,
        asset_create.gold_source_id,
    )
    if isinstance(result, Err):
        return Err(result.value)

    match result.value:
        case Some(existing):
            existing.name = asset_create.name
            existing.description = asset_create.description
            existing.tags = asset_create.tags
            session.add(existing)
            try:
                session.flush()
            except OperationalError as e:
                return Err(db_error_from(e))
            return Ok(AssetPublic.model_validate(existing, from_attributes=True))
        case _:
            new = Asset.model_validate(asset_create, from_attributes=True)
            session.add(new)
            try:
                session.flush()
            except OperationalError as e:
                return Err(db_error_from(e))
            return Ok(AssetPublic.model_validate(new, from_attributes=True))
