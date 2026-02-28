from enum import StrEnum

import sqlalchemy as sa
from sqlalchemy.exc import OperationalError
from sqlmodel import Field, Session, SQLModel, select

from app.errors import DBError, db_error_from
from app.result import Err, Nothing, Ok, Option, Result, Some


class GoldSourceType(StrEnum):
    ASSET_INVENTORY = "asset-inventory"


class GoldSourceMixin(SQLModel):
    """Mixin for models that are synced from an external gold source.

    Provides gold_source_id and gold_source_type columns with a composite
    unique constraint. Models should unpack the mixin's ``__table_args__``
    and add the composite index via ``gold_source_index``::

        class MyModel(GoldSourceMixin, SQLModel, table=True):
            __table_args__ = (
                *GoldSourceMixin.__table_args__,
                GoldSourceMixin.gold_source_index("my_model"),
            )
    """

    __table_args__ = (sa.UniqueConstraint("gold_source_type", "gold_source_id"),)

    gold_source_id: str = Field(nullable=False)
    gold_source_type: str = Field(nullable=False)

    @classmethod
    def gold_source_index(cls, table_name: str) -> sa.Index:
        """Create a composite index on (gold_source_type, gold_source_id).

        Each model must provide its own table name so the index gets a
        unique name (SQLAlchemy requires index names to be table-specific).
        """
        return sa.Index(f"ix_{table_name}_gold_source", "gold_source_type", "gold_source_id")

    @staticmethod
    def get_by_gold_source[T: SQLModel](
        session: Session,
        model_class: type[T],
        gold_source_type: str,
        gold_source_id: str,
    ) -> Result[Option[T], DBError]:
        """Query a model by its external gold source reference.

        Returns ``Ok(Some(record))`` on success, ``Ok(Nothing())`` when no
        record matches, or ``Err(DBError(...))`` on database operational errors.
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

        return Ok(Some(record))
