from app.models.base import BaseModel, GoldSourceMixin, TagsMixin


class MixinTestModel(GoldSourceMixin, TagsMixin, BaseModel, table=True):
    __tablename__ = "mixin_test_model"  # type: ignore[assignment]  # Pyright doesn't understand SQLAlchemy's declared_attr
    name: str = ""
