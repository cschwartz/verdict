# Decision: Result Type Error Handling Pattern

**Status:** Proposed
**Date:** 2026-02-23
**Ticket:** #19

## Context

The project currently lets database and operational errors propagate as exceptions. As the service layer grows (ingestion services, `get_by_gold_source`, audit log writes), we need a consistent error handling pattern that makes failure explicit in return types. This document evaluates Rust-like `Result` / functional `Either` approaches for Python and recommends an approach.

## Candidates Evaluated

### 1. `dry-python/returns` (v0.26.0)

**What it is:** A comprehensive functional programming toolkit providing `Result`, `Maybe`, `IO`, `Future`, context containers, do-notation, and composition utilities. Ships with a custom mypy plugin (17 files, ~53 KB) that hooks into mypy internals.

**Observed behavior:**

- Installed and ran on Python 3.14 without errors.
- `Success`/`Failure` wrappers work as expected; `@safe` decorator converts exceptions to `Failure` automatically.
- Chaining via `.bind()` works correctly.
- Pattern matching on `Success`/`Failure` works at runtime.
- Passes mypy --strict _without_ the plugin for basic `isinstance`/`match` narrowing. The plugin adds advanced narrowing for `.bind()` chains and do-notation — features we wouldn't use.

**Assessment:**

| Criterion              | Rating      | Notes                                                                                                                                                                                                                                                                                                             |
| ---------------------- | ----------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| API ergonomics         | Poor fit    | Uses `Success`/`Failure` naming (not `Ok`/`Err`). The full FP vocabulary (`IO`, `RequiresContext`, `Maybe`, pointfree functions, HKT) is far more than we need. 117 source files, 508 KB. Forces a paradigm shift on contributors.                                                                                |
| mypy --strict          | Conditional | Basic narrowing works without plugin. The custom mypy plugin (`returns.contrib.mypy.returns_plugin`) supports `mypy >=1.12, <1.18` — our project uses mypy >=1.19. PR #2321 to bump mypy has stalled since Dec 2025. Recurring breakage pattern: each mypy release breaks the plugin due to internal API changes. |
| Python 3.14            | Untested    | CI tests 3.10–3.13 only. No 3.14 classifier. Installed fine but not officially supported.                                                                                                                                                                                                                         |
| Library maturity       | Moderate    | 4,228 stars, ~771K monthly downloads. Single effective maintainer (sobolevn). Still in Beta (0.x) after 7 years. Recent commits are almost entirely automated dependency bumps.                                                                                                                                   |
| Overhead               | High        | Massive API surface. Contributors must learn FP concepts (monads, do-notation, HKT) to read service code.                                                                                                                                                                                                         |
| Scope fit              | Poor        | Designed for pervasive FP adoption, not selective service-layer use.                                                                                                                                                                                                                                              |
| SQLAlchemy integration | Neutral     | No conflicts found, but no helpers either.                                                                                                                                                                                                                                                                        |

**Verdict: Not recommended.** The mypy plugin version constraint conflicts with our toolchain, the API surface is far larger than needed, and the FP paradigm adds significant cognitive overhead for a compliance platform where most contributors will not have FP backgrounds.

---

### 2. `rustedpy/result` (v0.17.0)

**What it is:** A lightweight Rust-style `Ok`/`Err` Result type with combinators (`.map`, `.and_then`, `.unwrap_or`), pattern matching, `@as_result` decorator, and do-notation.

**Observed behavior:**

- Installed and ran on Python 3.14 without errors.
- `Ok`/`Err` API is clean and Pythonic.
- Pattern matching and isinstance narrowing both work.
- `.map()`, `.and_then()`, `.unwrap_or()` all work as expected.
- Passes mypy --strict cleanly (no plugin required).

**Assessment:**

| Criterion              | Rating   | Notes                                                                                                                                                                                                                                 |
| ---------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| API ergonomics         | Good     | Clean `Ok`/`Err` API. Familiar to anyone who's used Rust. Combinators (`.map`, `.and_then`) enable readable chaining.                                                                                                                 |
| mypy --strict          | Good     | No plugin required. Uses `TypeIs` for type guards. `isinstance` narrowing works correctly.                                                                                                                                            |
| Python 3.14            | Untested | CI only tests 3.8–3.12. Installed and worked fine in our probing but will never receive upstream fixes.                                                                                                                               |
| Library maturity       | Dead     | **Officially unmaintained as of Dec 2024** (Issue #201). Maintainer declared no more releases, fixes, or features. Co-maintainers concurred. ~2M monthly downloads are legacy momentum. Repo description changed to "NOT MAINTAINED." |
| Overhead               | Low      | Small, focused API. 669 LOC.                                                                                                                                                                                                          |
| Scope fit              | Good     | Works well when applied selectively.                                                                                                                                                                                                  |
| SQLAlchemy integration | Neutral  | No conflicts.                                                                                                                                                                                                                         |

**Notable fork:** `montasaurus/result` (61 stars, last pushed Dec 2025) has added Python 3.14 verification and strict pyright checks, but is not published to PyPI and self-describes as "not production tested."

**Verdict: Not recommended.** Despite having the best API design of the three libraries, the project is officially abandoned. Depending on an unmaintained library for core infrastructure is unacceptable. The co-maintainers' parting assessment is worth noting: "this style of programming simply does not lend itself well to the python ecosystem, both for technical and cultural reasons" — though we disagree for the narrow service-layer use case.

---

### 3. `poltergeist` (v0.10.0)

**What it is:** A minimal Rust-like Result type (~131 LOC across 3 files) providing `Ok`, `Err`, `Result`, `@catch`, and `@catch_async`. No combinators.

**Observed behavior:**

- Installed and ran on Python 3.14 without errors.
- `Ok`/`Err` pattern matching works at runtime.
- `@catch` decorator works for exception capture.
- Passes mypy --strict for exception-based errors (no plugin required, PEP 561 compliant).
- **Critical finding:** `Err` accepts plain dataclasses at _runtime_ but mypy rejects them: `_E = TypeVar("_E", bound=BaseException, covariant=True)`. Running `mypy --strict` on `Err(PlainNotFound(...))` produces `Value of type variable "_E" of "Err" cannot be "PlainNotFound" [type-var]`.

**Assessment:**

| Criterion              | Rating      | Notes                                                                                                                                                                                 |
| ---------------------- | ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------- |
| API ergonomics         | Adequate    | Clean but extremely limited. No `.map()`, `.and_then()`, `.is_ok()`. Only unwrap/pattern-match.                                                                                       |
| mypy --strict          | Constrained | Works for exception-typed errors. Rejects plain dataclass error types — confirmed by mypy output.                                                                                     |
| Python 3.14            | Untested    | CI only tests 3.10–3.11. Classifiers list 3.10–3.12. Installed fine. Pure Python, likely safe.                                                                                        |
| Library maturity       | Poor        | 151 stars, ~344 monthly downloads. Single maintainer, no commits since April 2024. Pre-Alpha status. Community maintenance PR from June 2025 went unanswered for 8 months.            |
| Overhead               | Very low    | 131 LOC. Zero dependencies.                                                                                                                                                           |
| Scope fit              | Good        | Minimal surface works for selective use.                                                                                                                                              |
| SQLAlchemy integration | Constrained | The `BaseException` bound on `Err` means error types must subclass `Exception`. Cannot use plain frozen dataclass error hierarchies, which is how we'd naturally model `NotFoundError | DBError`. |

**Verdict: Not recommended.** Too limited (no combinators), negligible community, dormant, and the `BaseException` constraint on `Err` prevents using typed dataclass error hierarchies — which is central to how we'd model domain errors.

---

### 4. Plain Union Return Types (`T | ErrorType`)

**What it is:** No library — functions return `T | NotFoundError | DBError` and callers use `isinstance` or `match` to narrow.

**Observed behavior:**

- Works with mypy --strict. `isinstance` and `match` both narrow correctly.
- No dependencies.

**Assessment:**

| Criterion      | Rating | Notes                                                                                                   |
| -------------- | ------ | ------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| API ergonomics | Poor   | No wrapper type means the success value and error types must be structurally distinct. Return type `str | NotFoundError`is ambiguous if the success type could also be an error type. No`.unwrap()` or chaining helpers. |
| mypy --strict  | Good   | Standard Python narrowing works.                                                                        |
| Python 3.14    | N/A    | No library dependency.                                                                                  |
| Overhead       | None   | No new concepts.                                                                                        |
| Scope fit      | Poor   | Doesn't compose well. Each caller must write its own narrowing logic with no shared vocabulary.         |

**Verdict: Not recommended.** Lacks the ergonomic benefits that motivate adopting Result types in the first place. No `Ok`/`Err` wrapper means no shared vocabulary, no `.unwrap()` convenience, and ambiguous return types when the success type overlaps with error types.

---

### 5. Roll Our Own Minimal `Result[T, E]` (Recommended)

**What it is:** A project-owned ~40-line module defining `Ok[T]`, `Err[E]`, and `Result[T, E] = Ok[T] | Err[E]` using Python 3.12+ type parameter syntax, `@dataclass(frozen=True, slots=True)`, and `@final`.

**Observed behavior:**

- Passes mypy --strict cleanly with zero configuration beyond what the project already has.
- Pattern matching works: `case Ok(value)` / `case Err(error)` with full type narrowing.
- `isinstance` narrowing works: `isinstance(r, Ok)` narrows to `Ok[T]`.
- No dependencies. No plugins. No version constraints.
- Error types are unconstrained — `Err[E]` works with dataclasses, exceptions, strings, or any type.
- Tested in a realistic service-layer function wrapping SQLModel queries with `IntegrityError` and `OperationalError` capture — works exactly as expected.

**mypy narrowing nuance:** Flat nested pattern matching (`case Err(NotFoundError(...))`) does not fully exhaust the union for mypy — it cannot narrow through `Err[NotFoundError | DBError]` to `Never` in the wildcard branch. Three approaches were tested and all pass mypy --strict:

1. **Two-level match** (recommended): match on `Ok`/`Err`, then match on the inner error type
2. **isinstance inside Err branch**: `if isinstance(error, NotFoundError)`
3. **Flat isinstance**: no pattern matching at all

The two-level match is the cleanest and most readable.

**Assessment:**

| Criterion              | Rating     | Notes                                                                                                                                                                                                 |
| ---------------------- | ---------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| API ergonomics         | Good       | `Ok`/`Err` vocabulary. `.unwrap()` and `.unwrap_or()` for convenience. Pattern matching for exhaustive handling.                                                                                      |
| mypy --strict          | Excellent  | Uses only standard Python typing constructs. No plugin. No version coupling. Two-level match pattern enables full exhaustiveness.                                                                     |
| Python 3.14            | Guaranteed | Pure Python, no dependencies. Uses stable language features (PEP 695 type params, dataclasses).                                                                                                       |
| Library maturity       | N/A        | We own it. No upstream risk.                                                                                                                                                                          |
| Overhead               | Very low   | ~40 lines. Contributors learn two types: `Ok` and `Err`.                                                                                                                                              |
| Scope fit              | Excellent  | We control exactly what's included. Add `.map()` or `.and_then()` only if/when needed.                                                                                                                |
| SQLAlchemy integration | Excellent  | Error types are unconstrained — `Err(NotFoundError(...))` works with plain dataclasses. `IntegrityError` and `OperationalError` are caught at the service boundary and wrapped in domain error types. |

## Recommendation

**Roll our own minimal `Result[T, E]` type.**

None of the three evaluated libraries are suitable:

- `returns` is too heavy, has mypy plugin version conflicts, and forces an FP paradigm.
- `result` is officially unmaintained.
- `poltergeist` is too limited, dormant, and constrains error types to `BaseException` subclasses.

A project-owned Result type gives us exactly what we need with zero external risk. The implementation is ~40 lines, passes mypy --strict, and integrates naturally with our SQLModel patterns.

### Implementation

Place in `app/result.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import NoReturn, final


@final
@dataclass(frozen=True, slots=True)
class Ok[T]:
    value: T

    def unwrap(self) -> T:
        return self.value

    def unwrap_or[D](self, default: D) -> T:
        return self.value


@final
@dataclass(frozen=True, slots=True)
class Err[E]:
    error: E

    def unwrap(self) -> NoReturn:
        raise RuntimeError(f"Called unwrap on Err: {self.error}")

    def unwrap_or[T](self, default: T) -> T:
        return default


type Result[T, E] = Ok[T] | Err[E]
```

### Domain Error Types

Define per-domain error types as frozen dataclasses in the relevant service module:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class NotFoundError:
    model: str
    key: str


@dataclass(frozen=True)
class DuplicateError:
    model: str
    key: str
    detail: str


@dataclass(frozen=True)
class DBError:
    message: str


type QueryError = NotFoundError | DBError
type WriteError = DuplicateError | DBError
```

### Service-Layer Usage

```python
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlmodel import Session, SQLModel, select

from app.result import Err, Ok, Result


def get_by_gold_source[T: SQLModel](
    session: Session,
    model_class: type[T],
    gold_source_type: str,
    gold_source_id: str,
) -> Result[T, QueryError]:
    try:
        statement = select(model_class).where(
            model_class.gold_source_type == gold_source_type,
            model_class.gold_source_id == gold_source_id,
        )
        record = session.exec(statement).first()
    except OperationalError as e:
        return Err(DBError(message=str(e)))

    if record is None:
        return Err(NotFoundError(model=model_class.__name__, key=gold_source_id))

    return Ok(record)
```

### Caller-Side Handling (Two-Level Match)

```python
match get_by_gold_source(session, Asset, "cmdb", "asset-001"):
    case Ok(asset):
        process(asset)  # asset is narrowed to Asset
    case Err(error):
        # Second-level match for exhaustive error handling
        match error:
            case NotFoundError(model, key):
                log.warning(f"{model} not found: {key}")
            case DBError(message):
                log.error(f"Database error: {message}")
                raise
```

The two-level match is necessary because mypy cannot narrow through nested destructuring of `Err(NotFoundError(...))` to full exhaustion. The outer match narrows `Result` to `Ok | Err`, and the inner match narrows the error union exhaustively.

## Open Design Questions: Async, Composition, and Growth

The recommendation above covers the synchronous, single-operation case. As the codebase grows — async database sessions, multi-step service operations, dependency injection — the minimal `Result[T, E]` type will need to evolve. This section investigates what that evolution requires and what design decisions we should make now to avoid painting ourselves into a corner.

### Async Functions and `Result[T, E]`

**Current state:** The database layer is synchronous (`sqlmodel.Session`, `psycopg2`). FastAPI route handlers are `async` but don't `await` database calls. `pytest-asyncio` is already a test dependency.

**Where async enters:** The architecture document specifies runners, evidence submission endpoints, external source ingestion, and config sync — all of which will involve I/O-bound operations (HTTP calls to external APIs, agent communication, potentially async DB sessions). Sprint 2's task framework and Sprint 3's evidence submission are the likely inflection points.

**The question:** Should `Result` have an async-aware variant, or do we just return `Result` from `async def` functions?

**Analysis:**

Returning `Result[T, E]` from an `async def` function works without any changes to the type:

```python
async def fetch_from_cmdb(
    client: httpx.AsyncClient,
    system_id: str,
) -> Result[CMDBSystem, IngestionError]:
    try:
        response = await client.get(f"/systems/{system_id}")
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        return Err(IngestionError(source="cmdb", detail=str(e)))

    return Ok(CMDBSystem.model_validate(response.json()))
```

The caller gets `Awaitable[Result[T, E]]`, which after `await` is just `Result[T, E]` — pattern matching and type narrowing work identically to the sync case. **No special `AsyncResult` or `FutureResult` wrapper is needed.**

The complexity arises when you want to **compose** async Result-returning operations — chaining multiple fallible async calls without nested match statements. This is the bind/map problem, discussed next.

### Bind (`and_then`) and Map: Do We Need Them?

**What they are:**

- **`map(f)`** — apply `f` to the success value, pass errors through unchanged. Transforms `Result[T, E]` → `Result[U, E]` via `f: T → U`.
- **`bind(f)`** / **`and_then(f)`** — apply `f` to the success value where `f` itself returns a `Result`. Chains fallible operations. Transforms `Result[T, E]` → `Result[U, E]` via `f: T → Result[U, E]`.

**The case for adding them:**

Consider a multi-step service operation — ingesting a CMDB system requires: fetch from external API → validate schema → check for duplicates → persist. Without `bind`, this becomes deeply nested:

```python
# Without bind — nested match pyramid
def ingest_system(session: Session, client: httpx.Client, system_id: str) -> Result[System, IngestionError]:
    match fetch_from_cmdb(client, system_id):
        case Err() as e:
            return e
        case Ok(raw):
            match validate_cmdb_schema(raw):
                case Err() as e:
                    return e
                case Ok(validated):
                    match check_duplicate(session, validated):
                        case Err() as e:
                            return e
                        case Ok(checked):
                            return persist_system(session, checked)
```

With `bind`, the same logic flattens:

```python
# With bind — flat chain
def ingest_system(session: Session, client: httpx.Client, system_id: str) -> Result[System, IngestionError]:
    return (
        fetch_from_cmdb(client, system_id)
        .bind(validate_cmdb_schema)
        .bind(lambda v: check_duplicate(session, v))
        .bind(lambda c: persist_system(session, c))
    )
```

**The case against adding them now:**

1. **Type inference breaks down.** Python's type system cannot infer the return type of a lambda inside `.bind()` — mypy will often widen to `Result[Unknown, Unknown]` or require explicit annotations. Rust gets this right because its type inference is global; Python's is local. This is the core reason `rustedpy/result`'s maintainers concluded the pattern "does not lend itself well to the python ecosystem."

2. **Error type widening.** If step 1 returns `Result[T, FetchError]` and step 2 returns `Result[U, ValidationError]`, what is the error type of the chain? In Rust, you'd use `From` trait conversions. In Python, you'd need a common error union or explicit mapping at each step. This adds ceremony that erodes the ergonomic benefit.

3. **Early-return with match is idiomatic Python.** The nested match pyramid looks bad in the abstract, but in practice Python developers reach for early returns:

```python
# Idiomatic Python — early return pattern
def ingest_system(session: Session, client: httpx.Client, system_id: str) -> Result[System, IngestionError]:
    result = fetch_from_cmdb(client, system_id)
    if isinstance(result, Err):
        return result

    result = validate_cmdb_schema(result.value)
    if isinstance(result, Err):
        return result

    result = check_duplicate(session, result.value)
    if isinstance(result, Err):
        return result

    return persist_system(session, result.value)
```

This is flat, readable, and mypy narrows every branch correctly. It's not as elegant as `.bind()` chains, but it's zero-magic and every Python developer can read it.

**Recommendation:** Do not add `bind` or `map` to the initial implementation. The early-return `isinstance` pattern is more readable in Python, has perfect type narrowing, and avoids the type inference problems that plague monadic chaining in Python. **Revisit if we find ourselves writing the same early-return boilerplate across 10+ service functions** — at that point, a helper like `result_chain` or a decorator could reduce repetition without the full monadic API.

### Async Bind: The Harder Problem

If we did add `bind`, the async variant is significantly more complex:

```python
# Hypothetical async bind — what it would look like
async def ingest_system_async(...) -> Result[System, IngestionError]:
    return await (
        await fetch_from_cmdb_async(client, system_id)
    ).bind_async(validate_cmdb_schema_async)
     .bind_async(lambda v: check_duplicate_async(session, v))
```

This requires `bind_async(f: T → Awaitable[Result[U, E]]) -> Awaitable[Result[U, E]]` — a method that returns an awaitable, which then needs to be awaited before the next `.bind_async()`. The chaining breaks because `await` is a statement, not an expression you can dot-chain from. Libraries like `dry-python/returns` solve this with `FutureResult` containers and custom do-notation — exactly the FP complexity we rejected.

**The early-return pattern handles async naturally:**

```python
async def ingest_system_async(
    session: AsyncSession, client: httpx.AsyncClient, system_id: str,
) -> Result[System, IngestionError]:
    result = await fetch_from_cmdb_async(client, system_id)
    if isinstance(result, Err):
        return result

    result = await validate_cmdb_schema_async(result.value)
    if isinstance(result, Err):
        return result

    result = await check_duplicate_async(session, result.value)
    if isinstance(result, Err):
        return result

    return await persist_system_async(session, result.value)
```

Same flat structure, same type narrowing, works identically to the sync version with `await` prepended. **This is the strongest argument for the early-return pattern over `.bind()` chains: it generalizes to async without any additional machinery.**

### Dependency Injection and Result-Returning Services

**Current DI pattern:** FastAPI's `Depends()` with `get_session()` generator. Tests override via `app.dependency_overrides`.

**How Result types interact with DI:**

Services that return `Result[T, E]` integrate cleanly with FastAPI's dependency injection. The route handler receives the service (or session), calls it, and matches on the result:

```python
@app.get("/systems/{gold_source_id}")
async def get_system(
    gold_source_id: str,
    session: Session = Depends(get_session),
) -> SystemResponse:
    match get_by_gold_source(session, System, "cmdb", gold_source_id):
        case Ok(system):
            return SystemResponse.from_model(system)
        case Err(error):
            match error:
                case NotFoundError():
                    raise HTTPException(status_code=404, detail="System not found")
                case DBError(message):
                    raise HTTPException(status_code=503, detail="Database unavailable")
```

**When services become injectable classes:** As the codebase grows, we may extract service classes (e.g., `IngestionService`, `EvidenceService`) that take a session and other dependencies in their constructor. Result types remain the return type of service methods — the DI pattern doesn't change the Result type design at all. The service class is the dependency; the Result is what its methods return.

```python
class IngestionService:
    def __init__(self, session: Session, client: httpx.Client) -> None:
        self.session = session
        self.client = client

    def ingest_system(self, system_id: str) -> Result[System, IngestionError]:
        # ... uses self.session and self.client
```

**Testing Result-returning services:** The existing transactional fixture pattern works perfectly — inject a test session, call the service method, assert on the `Result`:

```python
def test_ingest_system_not_found(db_session: Session) -> None:
    service = IngestionService(session=db_session, client=mock_client)
    result = service.ingest_system("nonexistent")
    assert isinstance(result, Err)
    assert isinstance(result.error, NotFoundError)
```

No mocking of error handling required — the Result makes the failure path a first-class value that tests can assert on directly. This is one of the strongest practical benefits of the pattern.

### What the Minimal Implementation Needs to Support Growth

Given the analysis above, the ~40-line implementation in the Recommendation section is sufficient for all near-term needs. Here is what it does **not** need yet, and when each addition would be warranted:

| Feature | When to add | Trigger |
|---|---|---|
| `map(f: T → U)` | When we repeatedly transform success values inline | 5+ service functions with `Ok(transform(result.value))` pattern |
| `bind(f: T → Result[U, E])` | When early-return boilerplate becomes excessive | 10+ service functions with 3+ chained fallible operations |
| `map_err(f: E → F)` | When we need to translate between error type hierarchies | Multiple service layers with distinct error unions |
| `AsyncResult` wrapper | Likely never | Only if `await` + early-return proves insufficient (unlikely) |
| `@safe` decorator | When wrapping many exception-throwing third-party calls | 5+ functions that are pure try/except → Result wrappers |
| `is_ok()` / `is_err()` | Convenience, low cost | Can add anytime; `isinstance` works fine meanwhile |

**The key design property to preserve:** `Result[T, E] = Ok[T] | Err[E]` as a plain union type alias. This ensures `isinstance` checks and `match` statements always work, and we never need a mypy plugin. Any methods we add to `Ok` and `Err` are convenience — the union type is the foundation.

### Decision: Start Minimal, Grow by Evidence

We are at the beginning of the codebase and can establish conventions that will scale. The right convention is:

1. **The `Result[T, E]` type as specified** — ~40 lines, `Ok`/`Err` dataclasses, `unwrap`/`unwrap_or`.
2. **Early-return `isinstance` pattern** for composing multiple Result-returning calls (sync and async).
3. **No `bind`/`map`/monadic chaining** until we have concrete evidence of repetitive boilerplate.
4. **No async-specific Result variants** — `async def → Result[T, E]` works out of the box.
5. **Service methods return `Result`; DI provides the dependencies** — these are orthogonal concerns.

This gives us a foundation that accommodates async, composition, and dependency injection without prematurely committing to abstractions we may not need. Each future addition (map, bind, safe decorator) can be added in isolation when the codebase demonstrates the need — and because `Result` is a plain union type, adding methods to `Ok`/`Err` is backwards-compatible.

## Boundary: Where to Use Result Types vs. Exceptions

| Layer                                                                              | Error Strategy                          | Rationale                                                                                                                                                                                                     |
| ---------------------------------------------------------------------------------- | --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Service functions** (queries, ingestion, writes)                                 | `Result[T, E]`                          | These are the functions where callers need to distinguish between success, "expected" failures (not found, duplicate), and operational errors. Result types make the failure modes explicit in the signature. |
| **FastAPI route handlers**                                                         | Consume `Result`, raise `HTTPException` | Routes match on `Result` and translate domain errors to HTTP status codes. This is the boundary where Results become HTTP responses.                                                                          |
| **Database/ORM layer** (`db.py`, models)                                           | Exceptions                              | SQLAlchemy and SQLModel use exceptions natively. Don't fight the framework. Service functions catch these and wrap them in Result types.                                                                      |
| **Unrecoverable failures** (config errors, startup failures, assertion violations) | Exceptions                              | These should crash the process. Result types add nothing when the only valid response is to abort.                                                                                                            |
| **Utilities and pure functions**                                                   | Exceptions or Result, case by case      | If a utility can fail in ways the caller should handle, use Result. If failure is a bug, raise.                                                                                                               |

The key principle: **Result types live at the service layer boundary.** They capture the expected failure modes of operations that interact with external state (database, external APIs). Everything below (ORM, drivers) uses exceptions. Everything above (routes) consumes Results and translates them.
