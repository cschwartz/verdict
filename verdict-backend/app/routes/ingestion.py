import httpx
from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.config import settings
from app.db import get_session
from app.deps import get_http_client
from app.result import unwrap_or_raise
from app.schemas.ingestion import FullIngestionResponse
from app.services.asset_ingestion import ingest_assets
from app.services.cmdb_ingestion import ingest_systems

router = APIRouter(tags=["ingestion"])


@router.post("/ingest", response_model=FullIngestionResponse)
def trigger_full_ingestion(
    session: Session = Depends(get_session),
    client: httpx.Client = Depends(get_http_client),
) -> FullIngestionResponse:
    assets = unwrap_or_raise(ingest_assets(session, client, settings.asset_inventory_url))
    systems = unwrap_or_raise(ingest_systems(session, client, settings.cmdb_url))
    session.commit()
    return FullIngestionResponse(
        assets_ingested=len(assets),
        systems_ingested=len(systems),
    )
