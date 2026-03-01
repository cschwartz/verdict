### Implement Standard Model

**Deps:** T9 — Policy Model

- Create `app/models/standard.py` with a `Standard` model using `TimestampMixin` + `GoldSourceMixin` + a composite index via `GoldSourceMixin.gold_source_index("standard")`. Fields: id, name, description, `policy_id` FK to Policy, metadata (JSON), timestamps.
- Configure cascade delete-orphan on the Policy → Standard relationship so deleting a Policy removes its Standards
- Define a SQLModel `Relationship` on Policy for navigating to its Standards
- Generate an Alembic migration for the Standard table
- Create `app/routes/standards.py` with endpoints: list standards (paginated, filterable by policy), get by ID, get by gold source
- Create a `StandardFactory` in `tests/factories/standard.py`
- Create tests: Standard is created with a Policy parent; creating a Standard without a valid Policy raises `IntegrityError`; deleting a Policy cascades to its Standards; gold source lookup works; route tests for listing, get by ID, get by gold source, and 404 handling

**Done:** Standard endpoints serve paginated lists, lookups by ID and gold source; Standard references its parent Policy via FK; creating a Standard without a valid Policy raises `IntegrityError`; deleting a Policy cascades to its Standards.
