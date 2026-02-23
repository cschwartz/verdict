from tests.models.mixin_test_model import MixinTestModel


def test_tags_round_trip(db_session):
    model = MixinTestModel(
        name="tagged",
        gold_source_type="test",
        gold_source_id="tags-1",
        tags=["os.linux.ubuntu-22.04", "role.database"],
    )
    db_session.add(model)
    db_session.flush()
    db_session.refresh(model)

    assert model.tags == ["os.linux.ubuntu-22.04", "role.database"]
    assert isinstance(model.tags, list)
