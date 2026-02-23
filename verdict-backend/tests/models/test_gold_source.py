import pytest
from sqlalchemy.exc import IntegrityError

from app.models.base import GoldSourceMixin
from tests.models.mixin_test_model import MixinTestModel


def test_get_by_gold_source_returns_record(db_session):
    model = MixinTestModel(
        name="findable",
        gold_source_type="test",
        gold_source_id="abc-123",
    )
    db_session.add(model)
    db_session.flush()

    result = GoldSourceMixin.get_by_gold_source(db_session, MixinTestModel, "test", "abc-123")

    assert result is not None
    assert result.id == model.id
    assert result.name == "findable"


def test_duplicate_gold_source_raises_integrity_error(db_session):
    model1 = MixinTestModel(
        name="first",
        gold_source_type="test",
        gold_source_id="dup-1",
    )
    db_session.add(model1)
    db_session.flush()

    model2 = MixinTestModel(
        name="second",
        gold_source_type="test",
        gold_source_id="dup-1",
    )
    db_session.add(model2)
    with pytest.raises(IntegrityError):
        db_session.flush()
