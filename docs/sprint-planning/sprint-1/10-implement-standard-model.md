### Implement Standard Model

**Deps:** T9 — Policy Model

- Add a `Standard` model to `app/models/policy.py` (or a separate `app/models/standard.py`) using `TimestampMixin` + `GoldSourceMixin`. Fields: id, name, description, `policy_id` FK to Policy, metadata (JSON), timestamps.
- Configure cascade delete-orphan on the Policy → Standard relationship so deleting a Policy removes its Standards
- Define a SQLModel `Relationship` on Policy for navigating to its Standards
- Generate an Alembic migration for the Standard table
- Create a `StandardFactory` in `tests/factories/policy.py` (or corresponding file)
- Create tests: Standard is created with a Policy parent; creating a Standard without a valid Policy raises `IntegrityError`; deleting a Policy cascades to its Standards; gold source lookup works

**Done:** Standard references its parent Policy via FK; creating a Standard without a valid Policy raises `IntegrityError`; deleting a Policy cascades to its Standards.
