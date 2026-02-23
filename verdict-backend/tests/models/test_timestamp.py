import time
from datetime import UTC, datetime

from tests.models.mixin_test_model import MixinTestModel


def test_created_at_auto_populated(db_session):
    model = MixinTestModel(
        name="test",
        gold_source_type="test",
        gold_source_id="created-at-1",
    )
    db_session.add(model)
    db_session.flush()
    db_session.refresh(model)

    assert model.created_at is not None
    assert (datetime.now(UTC) - model.created_at.replace(tzinfo=UTC)).total_seconds() < 5


def test_updated_at_changes_on_update(db_session):
    model = MixinTestModel(
        name="original",
        gold_source_type="test",
        gold_source_id="updated-at-1",
    )
    db_session.add(model)
    db_session.flush()
    db_session.refresh(model)
    original_updated_at = model.updated_at

    time.sleep(0.05)

    model.name = "modified"
    db_session.flush()
    db_session.refresh(model)

    assert model.updated_at > original_updated_at
