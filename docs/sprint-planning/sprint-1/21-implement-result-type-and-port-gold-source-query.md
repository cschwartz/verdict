# Implement Result Type and Port Gold Source Query #21

**Deps:** T2 - Base Mixins, T19 - Return Type Results

Decision document `docs/decisions/019-result-type-error-handling-pattern.md` recommends a project-owned minimal `Result[T, E]` type using `Ok[T]`/`Err[E]` dataclasses. This ticket implements that type and ports the existing `get_by_gold_source` function to use it, establishing the pattern for all future service-layer error handling.

- Create `app/result.py` with:
  - `Ok[T]` — `@final @dataclass(frozen=True, slots=True)` with `.unwrap() -> T` and `.unwrap_or(default) -> T`
  - `Err[E]` — `@final @dataclass(frozen=True, slots=True)` with `.unwrap() -> NoReturn` (raises `RuntimeError`) and `.unwrap_or(default) -> D`
  - `type Result[T, E] = Ok[T] | Err[E]`
- Define domain error types in `app/errors.py`:
  - `NotFoundError(model: str, key: str)` — frozen dataclass
  - `DuplicateError(model: str, key: str, detail: str)` — frozen dataclass
  - `DBError(message: str)` — frozen dataclass
  - `type QueryError = NotFoundError | DBError`
  - `type WriteError = DuplicateError | DBError`
- Port `GoldSourceMixin.get_by_gold_source` in `app/models/gold_source.py` to return `Result[T, QueryError]` instead of `T | None`:
  - Catch `OperationalError` and return `Err(DBError(...))`
  - Return `Err(NotFoundError(...))` when no record matches
  - Return `Ok(record)` on success
- Update existing tests in `tests/models/test_gold_source.py` to assert on `Ok`/`Err` values instead of `T | None`
- Add `tests/test_result.py` with tests for `Ok` and `Err`:
  - `Ok.unwrap()` returns the value
  - `Ok.unwrap_or(default)` returns the value (not the default)
  - `Err.unwrap()` raises `RuntimeError`
  - `Err.unwrap_or(default)` returns the default
  - `isinstance` narrowing works (assert `isinstance(Ok(1), Ok)` and not `isinstance(Ok(1), Err)`)
  - `match` statement narrowing works on `Result` (match `Ok` and `Err` branches)
  - Verify mypy accepts the two-level match pattern on `Result[T, QueryError]`

**Done:** `app/result.py` exists and passes `mypy --strict`; `get_by_gold_source` returns `Result[T, QueryError]`; callers can pattern-match or `isinstance`-check on `Ok`/`Err` with full type narrowing; all existing gold source tests pass against the new return type; `unwrap` and `unwrap_or` behave correctly for both `Ok` and `Err`.
