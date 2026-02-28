import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.config import settings
from app.db import get_session
from app.deps import get_http_client
from app.models.asset import Asset
from app.models.gold_source import GoldSourceMixin
from app.queries import get_by_id, get_paginated
from app.result import Err, Ok, unwrap_or_raise
from app.schemas.asset import AssetListResponse, AssetResponse, IngestionResponse
from app.services.asset_ingestion import ingest_assets

router = APIRouter(prefix="/assets", tags=["assets"])


@router.get("/", response_model=AssetListResponse)
def list_assets(
    session: Session = Depends(get_session),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> AssetListResponse:
    result = get_paginated(session, Asset, offset, limit)
    if isinstance(result, Err):
        raise HTTPException(status_code=503, detail=str(result))
    return AssetListResponse(
        assets=[AssetResponse.model_validate(a, from_attributes=True) for a in result.value.items],
        total=result.value.total,
    )


@router.get(
    "/by-gold-source/{source_type}/{source_id}",
    response_model=AssetResponse,
)
def get_asset_by_gold_source(
    source_type: str,
    source_id: str,
    session: Session = Depends(get_session),
) -> AssetResponse:
    result = GoldSourceMixin.get_by_gold_source(session, Asset, source_type, source_id)
    asset = unwrap_or_raise(result, not_found_detail="Asset not found")
    return AssetResponse.model_validate(asset, from_attributes=True)


@router.get("/{asset_id}", response_model=AssetResponse)
def get_asset(asset_id: int, session: Session = Depends(get_session)) -> AssetResponse:
    result = get_by_id(session, Asset, asset_id)
    asset = unwrap_or_raise(result, not_found_detail="Asset not found")
    return AssetResponse.model_validate(asset, from_attributes=True)


@router.post("/ingest", response_model=IngestionResponse)
def trigger_ingestion(
    session: Session = Depends(get_session),
    client: httpx.Client = Depends(get_http_client),
) -> IngestionResponse:
    result = ingest_assets(session, client, settings.asset_inventory_url)
    match result:
        case Ok(assets):
            session.commit()
            return IngestionResponse(ingested=len(assets))
        case Err(error):
            raise HTTPException(status_code=502, detail=str(error))
