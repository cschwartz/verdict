### Implement Statement Model

**Deps:** T10 — Standard Model

- Create `app/models/statement.py` with a `Statement` model using `TimestampMixin` + `GoldSourceMixin` + a composite index via `GoldSourceMixin.gold_source_index("statement")`. Fields: id, name, description, `standard_id` FK to Standard, metadata (JSON), timestamps.
- Configure cascade delete-orphan on the Standard → Statement relationship so deleting a Standard removes its Statements
- Define a SQLModel `Relationship` on Standard for navigating to its Statements
- Generate an Alembic migration for the Statement table
- Create `app/routes/statements.py` with endpoints: list statements (paginated, filterable by standard), get by ID, get by gold source
- Create a `StatementFactory` in `tests/factories/statement.py`
- Create tests: full Policy → Standard → Statement hierarchy can be created and navigated; cascade delete from Policy removes Standards and Statements; `get_by_gold_source()` works at each level of the hierarchy; route tests for listing, get by ID, get by gold source, and 404 handling

**Done:** Statement endpoints serve paginated lists, lookups by ID and gold source; full Policy → Standard → Statement hierarchy can be created and navigated; cascade delete from Policy removes Standards and Statements; gold source lookup works at each level.
