from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.db import get_session
from app.models.gold_source import GoldSourceMixin, GoldSourceType
from app.models.system import System, SystemPublic
from app.queries import get_by_id, get_paginated
from app.result import unwrap_optional_or_raise, unwrap_or_raise
from app.schemas.system import SystemListResponse

router = APIRouter(prefix="/systems", tags=["systems"])


def _to_public(system: System) -> SystemPublic:
    public = SystemPublic.model_validate(system, from_attributes=True)
    public.asset_ids = [a.id for a in system.assets if a.id is not None]
    return public


@router.get("/", response_model=SystemListResponse)
def list_systems(
    session: Session = Depends(get_session),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> SystemListResponse:
    paginated = unwrap_or_raise(get_paginated(session, System, offset, limit))
    return SystemListResponse(
        systems=[_to_public(s) for s in paginated.items],
        total=paginated.total,
    )


@router.get(
    "/by-gold-source/{source_type}/{source_id}",
    response_model=SystemPublic,
)
def get_system_by_gold_source(
    source_type: GoldSourceType,
    source_id: str,
    session: Session = Depends(get_session),
) -> SystemPublic:
    result = GoldSourceMixin.get_by_gold_source(session, System, source_type, source_id)
    system = unwrap_optional_or_raise(result, not_found_detail="System not found")
    return _to_public(system)


@router.get("/{system_id}", response_model=SystemPublic)
def get_system(system_id: int, session: Session = Depends(get_session)) -> SystemPublic:
    result = get_by_id(session, System, system_id)
    system = unwrap_optional_or_raise(result, not_found_detail="System not found")
    return _to_public(system)
