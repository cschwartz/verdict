import pytest

from app.db import engine
from tests.models.mixin_test_model import MixinTestModel


@pytest.fixture(scope="module", autouse=True)
def _create_test_table():
    MixinTestModel.__table__.create(engine, checkfirst=True)  # type: ignore[attr-defined]  # __table__ injected by SQLAlchemy metaclass
    yield
    MixinTestModel.__table__.drop(engine, checkfirst=True)  # type: ignore[attr-defined]  # __table__ injected by SQLAlchemy metaclass
