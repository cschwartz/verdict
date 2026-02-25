### Fix Mixin Type Safety and Column Reuse Bug

**Deps:** T2 — Base Model Mixins & Gold Source ID Pattern

Bug fix — resolves type checker errors and a latent runtime bug in the base model mixins introduced in T2.

**Problem 1 — Type errors on mixin-provided attributes:**
The mixins (`GoldSourceMixin`, `TagsMixin`, `TimestampMixin`) are plain Python classes, not `SQLModel` subclasses. Type checkers (mypy, pyright/pylance) do not understand that their annotated fields become valid SQLModel constructor parameters and instance attributes on concrete models. This produces false type errors on `gold_source_type`, `gold_source_id`, `tags`, and timestamp fields in both test and production code.

**Problem 2 — Latent `sa_column` reuse bug:**
Each mixin field uses `sa_column=sa.Column(...)`, which creates a single `Column` object instance. If two table models inherit the same mixin, SQLAlchemy raises `Column object 'X' already assigned to Table 'Y'`. This has not surfaced yet because only `MixinTestModel` uses the mixins, but it will break as soon as a second production model (e.g., `Asset`, `System`) is added.

**Fix:**

- Change each mixin to extend `SQLModel` (without `table=True`) so that the Pydantic/SQLModel metaclass recognizes mixin fields as proper model fields. This resolves all type checker errors.
- Replace `sa_column=sa.Column(...)` with `sa_type` + `sa_column_kwargs` on fields that require custom SQLAlchemy column types (`MutableJson`, `DateTime(timezone=True)`). This causes SQLModel to create a fresh `Column` instance per table model, fixing the column reuse bug. Fields with standard types (e.g., `str` on `GoldSourceMixin`) need no `sa_column` or `sa_type` at all.
- `sa_type` accepts type instances at runtime but mypy's stubs declare `type[Any]`; use `cast(type[Any], ...)` to satisfy the type checker without losing annotation-level type safety.

**Scope:**
- `app/models/gold_source.py` — `GoldSourceMixin(SQLModel)`, remove `sa_column` from `str` fields
- `app/models/tags.py` — `TagsMixin(SQLModel)`, replace `sa_column` with `sa_type=cast(type[Any], MutableJson)` + `sa_column_kwargs`
- `app/models/timestamp.py` — `TimestampMixin(SQLModel)`, replace `sa_column` with `sa_type=cast(type[Any], sa.DateTime(timezone=True))` + `sa_column_kwargs`
- `tests/models/mixin_test_model.py` — no changes expected (inheritance declaration stays the same)
- Verify existing tests pass without modification
- Verify mypy strict passes on mixin source files and test files

**Done:** All three mixins extend `SQLModel`; mypy strict reports no type errors on mixin definitions, `MixinTestModel`, and all tests in `tests/models/`; existing tests pass unchanged; two table models can inherit the same mixins without `Column already assigned` errors.
