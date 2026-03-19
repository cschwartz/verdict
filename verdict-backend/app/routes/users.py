import httpx
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.config import settings
from app.db import get_session
from app.deps import get_http_client
from app.models.user import User, UserPublic
from app.queries import get_by_id, get_paginated
from app.result import unwrap_optional_or_raise, unwrap_or_raise
from app.schemas.ingestion import UserIngestionResponse
from app.schemas.user import UserDetail, UserListResponse
from app.services.iam_ingestion import ingest_users

router = APIRouter(prefix="/users", tags=["users"])


def _to_user_detail(user: User) -> UserDetail:
    public = UserPublic.model_validate(user, from_attributes=True)
    return UserDetail(**public.model_dump(), roles=[role.name for role in user.roles])


@router.get("/", response_model=UserListResponse)
def list_users(
    session: Session = Depends(get_session),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> UserListResponse:
    paginated = unwrap_or_raise(
        get_paginated(session, User, offset, limit, public_class=UserPublic)
    )
    return UserListResponse(users=paginated.items, total=paginated.total)


@router.post("/ingest", response_model=UserIngestionResponse)
def trigger_user_ingestion(
    session: Session = Depends(get_session),
    client: httpx.Client = Depends(get_http_client),
) -> UserIngestionResponse:
    users = unwrap_or_raise(ingest_users(session, client, settings.iam_url))
    session.commit()
    return UserIngestionResponse(users_ingested=len(users))


@router.get("/{user_id}", response_model=UserDetail)
def get_user(user_id: int, session: Session = Depends(get_session)) -> UserDetail:
    result = get_by_id(session, User, user_id)
    user = unwrap_optional_or_raise(result, not_found_detail="User not found")
    return _to_user_detail(user)
