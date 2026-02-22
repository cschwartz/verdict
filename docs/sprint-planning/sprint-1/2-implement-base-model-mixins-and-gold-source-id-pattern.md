### Implement Base Model Mixins and Gold Source ID Pattern

**Deps:** T1 — Test Infrastructure and Database Fixtures

- Create `app/models/base.py` with a `TimestampMixin` that adds `created_at` (server-default to now) and `updated_at` (auto-updates on modification) columns
- Add a `GoldSourceMixin` to `app/models/base.py` with `gold_source_id: str` (indexed) and `gold_source_type: str` columns, plus a composite unique index on `(gold_source_type, gold_source_id)`
- Implement a `get_by_gold_source(session, model_class, gold_source_type, gold_source_id)` utility function in `app/models/base.py` that queries any model using `GoldSourceMixin` by its external reference
- Establish the tag storage pattern: a JSON column (via `sqlalchemy-json`) storing `list[str]` of dot-delimited hierarchical tags (e.g. `["os.linux.ubuntu-22.04"]`). Tag hierarchy querying is out of scope (Sprint 2).
- Create `tests/test_models_base.py` with tests using a temporary test-only SQLModel table model that composes both mixins and a tags column

**Done:** `created_at` is auto-populated on insert; `updated_at` changes on update; `get_by_gold_source()` returns the correct record; inserting a duplicate `(gold_source_type, gold_source_id)` raises `IntegrityError`; tags round-trip as `list[str]` through the JSON column.
