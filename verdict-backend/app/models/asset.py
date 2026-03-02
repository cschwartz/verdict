from sqlmodel import Field

from app.models.base import BaseModel, GoldSourceMixin, TagsMixin, TimestampMixin


class Asset(TimestampMixin, GoldSourceMixin, TagsMixin, BaseModel, table=True):
    __tablename__ = "asset"  # pyright: ignore[reportAssignmentType]  # SQLAlchemy declared_attr

    name: str = Field(nullable=False)
    description: str = Field(default="", nullable=False)
