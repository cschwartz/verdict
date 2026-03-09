from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.db import get_session
from app.models.asset import Asset, AssetPublic
from app.models.gold_source import GoldSourceMixin
from app.queries import get_by_id, get_paginated
from app.result import unwrap_optional_or_raise, unwrap_or_raise
from app.schemas.asset import AssetListResponse

router = APIRouter(prefix="/assets", tags=["assets"])


@router.get("/", response_model=AssetListResponse)
def list_assets(
    session: Session = Depends(get_session),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> AssetListResponse:
    paginated = unwrap_or_raise(
        get_paginated(session, Asset, offset, limit, public_class=AssetPublic)
    )
    return AssetListResponse(assets=paginated.items, total=paginated.total)


@router.get(
    "/by-gold-source/{source_type}/{source_id}",
    response_model=AssetPublic,
)
def get_asset_by_gold_source(
    source_type: str,
    source_id: str,
    session: Session = Depends(get_session),
) -> AssetPublic:
    result = GoldSourceMixin.get_by_gold_source(
        session, Asset, source_type, source_id, public_class=AssetPublic
    )
    return unwrap_optional_or_raise(result, not_found_detail="Asset not found")


@router.get("/{asset_id}", response_model=AssetPublic)
def get_asset(asset_id: int, session: Session = Depends(get_session)) -> AssetPublic:
    result = get_by_id(session, Asset, asset_id, public_class=AssetPublic)
    return unwrap_optional_or_raise(result, not_found_detail="Asset not found")
