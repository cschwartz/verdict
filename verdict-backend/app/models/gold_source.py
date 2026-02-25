import sqlalchemy as sa
from sqlmodel import Field, Session, SQLModel, select


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
    ) -> T | None:
        """Query a model by its external gold source reference.

        Returns the matching record, or None if no record matches the given
        gold_source_type and gold_source_id. Does not catch database errors --
        callers are responsible for handling connection or operational errors
        from the session.
        """
        if not issubclass(model_class, GoldSourceMixin):
            raise TypeError(f"{model_class.__name__} does not use GoldSourceMixin")

        statement = select(model_class).where(
            model_class.gold_source_type == gold_source_type,
            model_class.gold_source_id == gold_source_id,
        )
        return session.exec(statement).first()
