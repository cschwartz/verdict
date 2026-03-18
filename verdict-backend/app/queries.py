from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, final, overload

import sqlalchemy as sa
from sqlalchemy.exc import OperationalError
from sqlmodel import Session, func, select

from app.errors import DBError, db_error_from
from app.models.base_model import BaseModel, PublicModel
from app.models.gold_source import GoldSourceMixin, GoldSourceType
from app.models.user import Role, UserRole
from app.result import Err, Nothing, Ok, Option, Result, Some


@final
@dataclass(frozen=True, slots=True)
class PaginatedResult[T]:
    items: list[T]
    total: int


@overload
def get_by_id[T: BaseModel](
    session: Session,
    model_class: type[T],
    record_id: int,
) -> Result[Option[T], DBError]: ...


@overload
def get_by_id[T: BaseModel, P: PublicModel](
    session: Session,
    model_class: type[T],
    record_id: int,
    *,
    public_class: type[P],
) -> Result[Option[P], DBError]: ...


def get_by_id[T: BaseModel, P: PublicModel](
    session: Session,
    model_class: type[T],
    record_id: int,
    *,
    public_class: type[P] | None = None,
) -> Result[Option[Any], DBError]:
    try:
        record = session.get(model_class, record_id)
    except OperationalError as e:
        return Err(db_error_from(e))

    if record is None:
        return Ok(Nothing())

    if public_class is not None:
        return Ok(Some(public_class.model_validate(record, from_attributes=True)))

    return Ok(Some(record))


@overload
def get_paginated[T: BaseModel](
    session: Session,
    model_class: type[T],
    offset: int,
    limit: int,
) -> Result[PaginatedResult[T], DBError]: ...


@overload
def get_paginated[T: BaseModel, P: PublicModel](
    session: Session,
    model_class: type[T],
    offset: int,
    limit: int,
    *,
    public_class: type[P],
) -> Result[PaginatedResult[P], DBError]: ...


def get_paginated[T: BaseModel, P: PublicModel](
    session: Session,
    model_class: type[T],
    offset: int,
    limit: int,
    *,
    public_class: type[P] | None = None,
) -> Result[PaginatedResult[Any], DBError]:
    try:
        total = session.exec(select(func.count()).select_from(model_class)).one()
        items = list(
            session.exec(
                select(model_class).order_by(model_class.id).offset(offset).limit(limit)  # type: ignore[arg-type]  # mypy sees int | None (instance type) instead of SQLAlchemy column descriptor
            ).all()
        )
    except OperationalError as e:
        return Err(db_error_from(e))

    if public_class is not None:
        public_items = [public_class.model_validate(i, from_attributes=True) for i in items]
        return Ok(PaginatedResult(items=public_items, total=total))

    return Ok(PaginatedResult(items=items, total=total))


@overload
def get_role_by_name(session: Session, name: str) -> Result[Option[Role], DBError]: ...


@overload
def get_role_by_name[P: PublicModel](
    session: Session, name: str, *, public_class: type[P]
) -> Result[Option[P], DBError]: ...


def get_role_by_name[P: PublicModel](
    session: Session, name: str, *, public_class: type[P] | None = None
) -> Result[Option[Any], DBError]:
    try:
        role = session.exec(select(Role).where(Role.name == name)).first()
    except OperationalError as e:
        return Err(db_error_from(e))
    if role is None:
        return Ok(Nothing())
    if public_class is not None:
        return Ok(Some(public_class.model_validate(role, from_attributes=True)))
    return Ok(Some(role))


def upsert_by_gold_source[T: BaseModel, P: PublicModel](
    session: Session,
    model_class: type[T],
    gold_source_type: GoldSourceType,
    gold_source_id: str,
    *,
    public_class: type[P],
    on_existing: Callable[[T], None],
    make_new: Callable[[], T],
) -> Result[P, DBError]:
    """Select-then-insert upsert by gold source identity.

    Only OperationalError is caught on flush — IntegrityError from a concurrent
    insert is not handled. This is intentional: all callers are single-threaded
    batch operations (ingestion services, config sync), so the race cannot occur.
    If concurrent callers are ever introduced, add IntegrityError handling here.
    """
    match GoldSourceMixin.get_by_gold_source(
        session, model_class, gold_source_type, gold_source_id
    ):
        case Err(e):
            return Err(e)
        case Ok(Some(record)):
            on_existing(record)
            session.add(record)
        case Ok(Nothing()) | _:
            record = make_new()
            session.add(record)
    try:
        session.flush()
    except OperationalError as e:
        return Err(db_error_from(e))
    return Ok(public_class.model_validate(record, from_attributes=True))


def sync_join_table(
    session: Session,
    owner_col: sa.Column[int],
    owner_id: int,
    member_col: sa.Column[int],
    desired_ids: list[int],
) -> Result[None, DBError]:
    """Sync a join table so the member set matches desired_ids exactly
    (add missing, remove extra)."""
    try:
        existing_ids = {
            row[0]
            for row in session.execute(sa.select(member_col).where(owner_col == owner_id)).all()
        }
        to_remove = existing_ids - set(desired_ids)
        to_add = set(desired_ids) - existing_ids
        if to_remove:
            session.execute(
                sa.delete(owner_col.table).where(owner_col == owner_id, member_col.in_(to_remove))
            )
        for mid in to_add:
            session.execute(
                sa.insert(owner_col.table).values({owner_col.key: owner_id, member_col.key: mid})
            )
    except OperationalError as e:
        return Err(db_error_from(e))
    return Ok(None)


def sync_user_roles(
    session: Session,
    user_id: int,
    desired_role_ids: list[int],
) -> Result[None, DBError]:
    """Set a user's roles to exactly the provided list (add missing, remove extra)."""
    t = UserRole.__table__  # type: ignore[attr-defined]  # SQLModel does not expose __table__ in stubs but it exists on table=True models
    return sync_join_table(session, t.c.user_id, user_id, t.c.role_id, desired_role_ids)
