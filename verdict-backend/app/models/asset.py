from sqlmodel import Field, SQLModel

from app.models.base import GoldSourceMixin, TagsMixin, TimestampMixin


class Asset(TimestampMixin, GoldSourceMixin, TagsMixin, SQLModel, table=True):
    __tablename__ = "asset"  # pyright: ignore[reportAssignmentType]  # SQLAlchemy declared_attr
    __table_args__ = (  # type: ignore[assignment]
        *GoldSourceMixin.__table_args__,
        GoldSourceMixin.gold_source_index("asset"),
    )

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(nullable=False)
    description: str = Field(default="", nullable=False)
