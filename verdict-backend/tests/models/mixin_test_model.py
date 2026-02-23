from sqlmodel import Field, SQLModel

from app.models.base import GoldSourceMixin, TagsMixin, TimestampMixin


class MixinTestModel(TimestampMixin, GoldSourceMixin, TagsMixin, SQLModel, table=True):
    __tablename__ = "mixin_test_model"
    id: int | None = Field(default=None, primary_key=True)
    name: str = ""
