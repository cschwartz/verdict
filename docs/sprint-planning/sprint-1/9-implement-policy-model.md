### Implement Policy Model

**Deps:** T2 — Base Model Mixins and Gold Source ID Pattern, T8 — OSCAL Pydantic Library Evaluation

The T8 research recommendation informs whether this model wraps an external OSCAL library or uses custom Pydantic/SQLModel definitions.

- Create `app/models/policy.py` with a `Policy` model using `TimestampMixin` + `GoldSourceMixin`. Fields: id, name, description, metadata (JSON, for OSCAL-specific fields), timestamps.
- Generate an Alembic migration for the Policy table
- Create `tests/factories/policy.py` with a `PolicyFactory`
- Create tests: Policy can be created with a gold source ID and metadata; `get_by_gold_source()` returns the correct Policy; duplicate gold source IDs raise `IntegrityError`

**Done:** Policy can be created with gold source ID and metadata; `get_by_gold_source()` returns correct Policy; factory produces valid instances.
