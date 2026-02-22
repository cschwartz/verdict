### Implement Statement Model

**Deps:** T10 — Standard Model

- Add a `Statement` model to the governance models file using `TimestampMixin` + `GoldSourceMixin`. Fields: id, name, description, `standard_id` FK to Standard, metadata (JSON), timestamps.
- Configure cascade delete-orphan on the Standard → Statement relationship so deleting a Standard removes its Statements
- Define a SQLModel `Relationship` on Standard for navigating to its Statements
- Generate an Alembic migration for the Statement table
- Create a `StatementFactory` in the governance factories file
- Create tests: full Policy → Standard → Statement hierarchy can be created and navigated; cascade delete from Policy removes Standards and Statements; `get_by_gold_source()` works at each level of the hierarchy

**Done:** Full Policy → Standard → Statement hierarchy can be created and navigated; cascade delete from Policy removes Standards and Statements; gold source lookup works at each level.
