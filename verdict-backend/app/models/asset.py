from sqlmodel import Field

from app.models.base import BaseModel, GoldSourceMixin, TagsMixin, TimestampMixin


class Asset(TimestampMixin, GoldSourceMixin, TagsMixin, BaseModel, table=True):
    __tablename__ = "asset"  # pyright: ignore[reportAssignmentType]  # SQLAlchemy declared_attr
    __table_args__ = (  # type: ignore[assignment]
        *GoldSourceMixin.__table_args__,
        GoldSourceMixin.gold_source_index("asset"),
    )

    name: str = Field(nullable=False)
    description: str = Field(default="", nullable=False)
