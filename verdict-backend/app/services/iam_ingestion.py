import logging
from urllib.parse import quote

import httpx
from pydantic import TypeAdapter
from sqlalchemy.exc import OperationalError
from sqlmodel import Session

from app.errors import DBError, FetchError, IngestionError, RemoteValidationError, db_error_from
from app.http import fetch_json
from app.models.gold_source import GoldSourceMixin, GoldSourceType
from app.models.user import Role, RolePublic, User, UserPublic
from app.queries import sync_user_roles, upsert_by_gold_source
from app.result import Err, Nothing, Ok, Result, Some
from app.schemas.external.iam import IAMUserDetail, IAMUserIndexItem

logger = logging.getLogger(__name__)

_index_adapter = TypeAdapter(list[IAMUserIndexItem])
_detail_adapter = TypeAdapter(IAMUserDetail)

type SourceError = FetchError | RemoteValidationError


def fetch_index(
    client: httpx.Client,
    url: str,
) -> Result[list[IAMUserIndexItem], SourceError]:
    return fetch_json(client, url, _index_adapter)


def fetch_detail(
    client: httpx.Client,
    url: str,
    user_id: str,
) -> Result[IAMUserDetail, SourceError]:
    return fetch_json(client, f"{url}/{quote(user_id, safe='')}", _detail_adapter)


def _upsert_user(
    session: Session,
    detail: IAMUserDetail,
) -> Result[UserPublic, DBError]:
    def on_existing(existing: User) -> None:
        existing.username = detail.username
        existing.email = detail.email

    def make_new() -> User:
        return User(
            username=detail.username,
            email=detail.email,
            is_active=True,
            gold_source_type=GoldSourceType.IAM_USER,
            gold_source_id=detail.id,
        )

    return upsert_by_gold_source(
        session,
        User,
        GoldSourceType.IAM_USER,
        detail.id,
        public_class=UserPublic,
        on_existing=on_existing,
        make_new=make_new,
    )


def _resolve_role_ids(
    session: Session,
    group_ids: list[str],
) -> Result[list[int], DBError]:
    """Map IAM group IDs to local Role IDs. Skips groups with no matching role (logs warning)."""
    role_ids: list[int] = []
    for gid in group_ids:
        result = GoldSourceMixin.get_by_gold_source(
            session,
            Role,
            GoldSourceType.IAM_GROUP,
            gid,
            public_class=RolePublic,
        )
        if isinstance(result, Err):
            return Err(result.value)
        match result.value:
            case Some(role):
                role_ids.append(role.id)
            case Nothing():
                logger.warning("IAM group %s has no corresponding Role; skipping", gid)
    return Ok(role_ids)


def ingest_users(
    session: Session,
    client: httpx.Client,
    url: str,
) -> Result[list[UserPublic], IngestionError]:
    index_result = fetch_index(client, url)
    if isinstance(index_result, Err):
        return Err(index_result.value)

    details: list[IAMUserDetail] = []
    for index_item in index_result.value:
        detail_result = fetch_detail(client, url, index_item.id)
        if isinstance(detail_result, Err):
            return Err(detail_result.value)
        details.append(detail_result.value)

    users: list[UserPublic] = []
    for detail in details:
        upsert_result = _upsert_user(session, detail)
        if isinstance(upsert_result, Err):
            return Err(upsert_result.value)
        user_public = upsert_result.value

        role_ids_result = _resolve_role_ids(session, detail.groups)
        if isinstance(role_ids_result, Err):
            return Err(role_ids_result.value)

        sync_result = sync_user_roles(session, user_public.id, role_ids_result.value)
        if isinstance(sync_result, Err):
            return Err(sync_result.value)

        users.append(user_public)

    try:
        session.flush()
    except OperationalError as e:
        return Err(db_error_from(e))
    return Ok(users)
