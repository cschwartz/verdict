from pathlib import Path

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.config import settings
from app.db import get_session
from app.result import unwrap_or_raise
from app.schemas.sync import SyncResponse
from app.services.config_sync import sync_config

router = APIRouter(tags=["sync"])


@router.post("/sync", response_model=SyncResponse)
def trigger_sync(
    session: Session = Depends(get_session),
) -> SyncResponse:
    result = sync_config(session, Path(settings.config_basedir))
    response = unwrap_or_raise(result)
    session.commit()
    return response
