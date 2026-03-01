import logging

import httpx
from pydantic import TypeAdapter
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.exc import OperationalError
from sqlmodel import Session

from app.errors import DBError, FetchError, IngestionError, db_error_from
from app.errors import ValidationError as AppValidationError
from app.models.asset import Asset
from app.models.gold_source import GoldSourceMixin, GoldSourceType
from app.result import Err, Ok, Result, Some
from app.schemas.external.asset_inventory import AssetDetail, AssetIndexItem

logger = logging.getLogger(__name__)

_index_adapter = TypeAdapter(list[AssetIndexItem])
_detail_adapter = TypeAdapter(AssetDetail)

type SourceError = FetchError | AppValidationError


def fetch_index(
    client: httpx.Client,
    url: str,
) -> Result[list[AssetIndexItem], SourceError]:
    """Fetch the asset index from the external inventory."""
    try:
        response = client.get(url)
        response.raise_for_status()
    except httpx.HTTPError as e:
        return Err(FetchError(url=url, raw=str(e)))

    try:
        items = _index_adapter.validate_json(response.content)
    except PydanticValidationError as e:
        logger.error("Schema mismatch from asset inventory index: %s", e)
        return Err(AppValidationError(raw=str(e)))

    return Ok(items)


def fetch_detail(
    client: httpx.Client,
    url: str,
    item_id: str,
) -> Result[AssetDetail, SourceError]:
    """Fetch a single asset's detail from the external inventory."""
    detail_url = f"{url}/{item_id}"
    try:
        response = client.get(detail_url)
        response.raise_for_status()
    except httpx.HTTPError as e:
        return Err(FetchError(url=detail_url, raw=str(e)))

    try:
        detail = _detail_adapter.validate_json(response.content)
    except PydanticValidationError as e:
        logger.error("Schema mismatch from asset inventory detail %s: %s", item_id, e)
        return Err(AppValidationError(raw=str(e)))

    return Ok(detail)


def to_asset(detail: AssetDetail) -> Asset:
    """Convert an external asset detail to a verdict Asset."""
    return Asset(
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
) -> Result[list[Asset], IngestionError]:
    """Fetch assets from the external inventory and upsert them.

    Three phases: fetch index, fetch detail for each, convert and upsert.
    Does not commit — the caller owns the session lifecycle.
    """
    index_result = fetch_index(client, url)
    if isinstance(index_result, Err):
        return Err(index_result.value)

    assets: list[Asset] = []
    for index_item in index_result.value:
        detail_result = fetch_detail(client, url, index_item.id)
        if isinstance(detail_result, Err):
            return Err(detail_result.value)

        asset = to_asset(detail_result.value)
        upsert_result = _upsert_asset(session, asset)
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
    asset: Asset,
) -> Result[Asset, DBError]:
    """Look up an existing asset by gold source or create a new one."""
    result = GoldSourceMixin.get_by_gold_source(
        session,
        Asset,
        asset.gold_source_type,
        asset.gold_source_id,
    )
    if isinstance(result, Err):
        return result

    match result.value:
        case Some(existing):
            existing.name = asset.name
            existing.description = asset.description
            existing.tags = asset.tags
            session.add(existing)
            return Ok(existing)
        case _:
            session.add(asset)
            return Ok(asset)
