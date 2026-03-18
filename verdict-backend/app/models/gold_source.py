from enum import StrEnum
from typing import Any, overload

import sqlalchemy as sa
from sqlalchemy.exc import OperationalError
from sqlmodel import Field, Session, SQLModel, select

from app.errors import DBError, db_error_from
from app.models.base_model import BaseModel, PublicModel
from app.result import Err, Nothing, Ok, Option, Result, Some


class GoldSourceType(StrEnum):
    ASSET_INVENTORY = "asset-inventory"
    CMDB = "cmdb"
    IAM_USER = "iam_user"
    IAM_GROUP = "iam_group"
    LOCAL_USER = "local_user"


class GoldSourceMixin(SQLModel):
    """Mixin for models that are synced from an external gold source.

    Provides gold_source_id and gold_source_type columns with a composite
    unique constraint (which also serves as an index for lookups).
    """

    __table_args__ = (sa.UniqueConstraint("gold_source_type", "gold_source_id"),)

    gold_source_id: str = Field(nullable=False)
    gold_source_type: GoldSourceType = Field(nullable=False, sa_type=sa.String())  # type: ignore[call-overload]  # SQLModel Field stub types sa_type as type[Any] but accepts TypeEngine instances too

    @staticmethod
    @overload
    def get_by_gold_source[T: BaseModel](
        session: Session,
        model_class: type[T],
        gold_source_type: GoldSourceType,
        gold_source_id: str,
    ) -> Result[Option[T], DBError]: ...

    @staticmethod
    @overload
    def get_by_gold_source[T: BaseModel, P: PublicModel](
        session: Session,
        model_class: type[T],
        gold_source_type: GoldSourceType,
        gold_source_id: str,
        *,
        public_class: type[P],
    ) -> Result[Option[P], DBError]: ...

    @staticmethod
    def get_by_gold_source[T: BaseModel, P: PublicModel](
        session: Session,
        model_class: type[T],
        gold_source_type: GoldSourceType,
        gold_source_id: str,
        *,
        public_class: type[P] | None = None,
    ) -> Result[Option[Any], DBError]:
        """Query a model by its external gold source reference.

        Returns ``Ok(Some(record))`` on success, ``Ok(Nothing())`` when no
        record matches, or ``Err(DBError(...))`` on database operational errors.

        When *public_class* is provided, the record is validated into that type
        before being returned, narrowing optional fields like ``id`` and
        timestamps.
        """
        if not issubclass(model_class, GoldSourceMixin):
            raise TypeError(f"{model_class.__name__} does not use GoldSourceMixin")

        try:
            statement = select(model_class).where(
                model_class.gold_source_type == gold_source_type,
                model_class.gold_source_id == gold_source_id,
            )
            record = session.exec(statement).first()
        except (
            OperationalError
        ) as e:  # intentionally narrow — programming errors (e.g. IntegrityError) should propagate
            return Err(db_error_from(e))

        if record is None:
            return Ok(Nothing())

        if public_class is not None:
            return Ok(Some(public_class.model_validate(record, from_attributes=True)))

        return Ok(Some(record))
