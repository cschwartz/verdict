from dataclasses import dataclass
from typing import Any, final, overload

from sqlalchemy.exc import OperationalError
from sqlmodel import Session, func, select

from app.errors import DBError, db_error_from
from app.models.base_model import BaseModel, PublicModel
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
