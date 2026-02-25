import sqlalchemy as sa
from sqlalchemy.exc import OperationalError
from sqlmodel import Field, Session, SQLModel, select

from app.errors import DBError
from app.result import Err, Nothing, Ok, Option, Result, Some


class GoldSourceMixin(SQLModel):
    """Mixin for models that are synced from an external gold source.

    Provides gold_source_id and gold_source_type columns with a composite
    unique constraint. Models that need additional __table_args__ must
    unpack this mixin's args::

        class MyModel(GoldSourceMixin, SQLModel, table=True):
            __table_args__ = (
                *GoldSourceMixin.__table_args__,
                sa.Index("ix_my_model_custom", "some_field"),
            )
    """

    __table_args__ = (sa.UniqueConstraint("gold_source_type", "gold_source_id"),)

    gold_source_id: str = Field(index=True, nullable=False)
    gold_source_type: str = Field(nullable=False)

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
        except OperationalError as e:
            return Err(DBError(message=str(e)))

        if record is None:
            return Ok(Nothing())

        return Ok(Some(record))
