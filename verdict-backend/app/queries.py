from dataclasses import dataclass
from typing import final

from sqlalchemy.exc import OperationalError
from sqlmodel import Session, SQLModel, func, select

from app.errors import DBError, db_error_from
from app.result import Err, Nothing, Ok, Option, Result, Some


@final
@dataclass(frozen=True, slots=True)
class PaginatedResult[T]:
    items: list[T]
    total: int


def get_by_id[T: SQLModel](
    session: Session,
    model_class: type[T],
    record_id: int,
) -> Result[Option[T], DBError]:
    try:
        record = session.get(model_class, record_id)
    except OperationalError as e:
        return Err(db_error_from(e))

    if record is None:
        return Ok(Nothing())
    return Ok(Some(record))


def get_paginated[T: SQLModel](
    session: Session,
    model_class: type[T],
    offset: int,
    limit: int,
) -> Result[PaginatedResult[T], DBError]:
    try:
        total = session.exec(select(func.count()).select_from(model_class)).one()
        items = list(session.exec(select(model_class).offset(offset).limit(limit)).all())
    except OperationalError as e:
        return Err(db_error_from(e))

    return Ok(PaginatedResult(items=items, total=total))
