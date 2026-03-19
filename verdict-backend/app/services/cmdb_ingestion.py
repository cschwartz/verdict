from urllib.parse import quote

import httpx
from pydantic import TypeAdapter
from sqlalchemy.exc import OperationalError
from sqlmodel import Session

from app.errors import (
    DBError,
    FetchError,
    IngestionError,
    RemoteValidationError,
    db_error_from,
)
from app.http import fetch_json
from app.models.asset import Asset, AssetPublic
from app.models.gold_source import GoldSourceMixin, GoldSourceType
from app.models.system import System, SystemCreate, SystemPublic, asset_system
from app.queries import sync_join_table, upsert_by_gold_source
from app.result import Err, Nothing, Ok, Result, Some
from app.schemas.external.cmdb import SystemDetail, SystemIndexItem

_index_adapter = TypeAdapter(list[SystemIndexItem])
_detail_adapter = TypeAdapter(SystemDetail)

type SourceError = FetchError | RemoteValidationError


def fetch_index(
    client: httpx.Client,
    url: str,
) -> Result[list[SystemIndexItem], SourceError]:
    return fetch_json(client, url, _index_adapter)


def fetch_detail(
    client: httpx.Client,
    url: str,
    item_id: str,
) -> Result[SystemDetail, SourceError]:
    return fetch_json(client, f"{url}/{quote(item_id, safe='')}", _detail_adapter)


def to_system(detail: SystemDetail) -> SystemCreate:
    return SystemCreate(
        primary_fqdn=detail.primary_fqdn,
        tags=detail.tags,
        gold_source_id=detail.id,
        gold_source_type=GoldSourceType.CMDB,
    )


def _resolve_asset_ids(
    session: Session,
    gold_source_ids: list[str],
    url: str,
) -> Result[list[int], RemoteValidationError | DBError]:
    asset_ids: list[int] = []
    for gs_id in gold_source_ids:
        result = GoldSourceMixin.get_by_gold_source(
            session,
            Asset,
            GoldSourceType.ASSET_INVENTORY,
            gs_id,
            public_class=AssetPublic,
        )
        if isinstance(result, Err):
            return Err(result.value)
        match result.value:
            case Some(asset):
                asset_ids.append(asset.id)
            case Nothing():
                return Err(
                    RemoteValidationError(
                        url=url,
                        raw=f"unresolvable asset reference: {gs_id}",
                    )
                )
    return Ok(asset_ids)


def _upsert_system(
    session: Session,
    system_create: SystemCreate,
) -> Result[SystemPublic, DBError]:
    def on_existing(existing: System) -> None:
        existing.primary_fqdn = system_create.primary_fqdn
        existing.tags = system_create.tags

    def make_new() -> System:
        return System.model_validate(system_create, from_attributes=True)

    return upsert_by_gold_source(
        session,
        System,
        system_create.gold_source_type,
        system_create.gold_source_id,
        public_class=SystemPublic,
        on_existing=on_existing,
        make_new=make_new,
    )


def _sync_asset_links(
    session: Session,
    system_id: int,
    desired_asset_ids: list[int],
) -> Result[None, DBError]:
    return sync_join_table(
        session, asset_system.c.system_id, system_id, asset_system.c.asset_id, desired_asset_ids
    )


def ingest_systems(
    session: Session,
    client: httpx.Client,
    url: str,
) -> Result[list[SystemPublic], IngestionError]:
    index_result = fetch_index(client, url)
    if isinstance(index_result, Err):
        return Err(index_result.value)

    details: list[SystemDetail] = []
    for index_item in index_result.value:
        detail_result = fetch_detail(client, url, index_item.id)
        if isinstance(detail_result, Err):
            return Err(detail_result.value)
        details.append(detail_result.value)

    resolved_assets: dict[str, list[int]] = {}
    for detail in details:
        if detail.asset_gold_source_ids:
            resolve_result = _resolve_asset_ids(session, detail.asset_gold_source_ids, url)
            if isinstance(resolve_result, Err):
                return Err(resolve_result.value)
            resolved_assets[detail.id] = resolve_result.value
        else:
            resolved_assets[detail.id] = []

    systems: list[SystemPublic] = []
    for detail in details:
        system_create = to_system(detail)
        upsert_result = _upsert_system(session, system_create)
        if isinstance(upsert_result, Err):
            return Err(upsert_result.value)
        system_public = upsert_result.value
        sync_result = _sync_asset_links(session, system_public.id, resolved_assets[detail.id])
        if isinstance(sync_result, Err):
            return Err(sync_result.value)
        systems.append(system_public)

    try:
        session.flush()
    except OperationalError as e:
        return Err(db_error_from(e))
    return Ok(systems)
