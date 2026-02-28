# Backend Patterns

## Error Handling

The backend uses typed Result and Option types instead of exceptions for recoverable errors.

A `Result[T, E]` is either `Ok(value)` or `Err(error)`, where the error type is explicit in the signature. An `Option[T]` is either `Some(value)` or `Nothing()`, representing the presence or absence of a value. These compose naturally: a database lookup returns `Result[Option[T], DBError]`, meaning the operation itself can fail (Err) or succeed with either a found record (Ok(Some)) or no record (Ok(Nothing)).

All error types inherit from `AppError`, an abstract base class that enforces a two-level message contract. Each error exposes a `message` property (safe to return to clients) and a `detail` property (for internal logging only, may contain URLs, SQL statements, or driver messages). `__str__` returns `message`, so errors are safe by default anywhere they are converted to strings. Error types store their raw diagnostic data in fields and compute both properties from them.

Error types are domain-specific dataclasses defined in `app/errors.py`. They form unions that describe what can go wrong in each context: `IngestionError` covers fetch failures, schema validation errors, and database errors. Functions declare which error union they can produce, and callers handle each variant explicitly.

Routes bridge typed errors to HTTP responses via two helpers: `unwrap_or_raise` converts a `Result[T, E]` into either the unwrapped value or an HTTP error, while `unwrap_optional_or_raise` handles `Result[Option[T], E]` with an additional Nothing-to-404 mapping. Both log the error detail internally and return only the safe message to clients.

The SQLAlchemy engine is configured with `hide_parameters=True`, which redacts SQL parameter values from exception messages and query logging at the driver level. This is a defence-in-depth measure alongside the `AppError` message/detail separation.

Exceptions are reserved for programming errors (bugs) that should propagate and crash. Operational errors (network failures, missing records, schema mismatches) flow through Result types so they can be handled, composed, and tested without try/except.

## Ingestion Pipeline

External data is ingested through a three-phase pipeline that separates fetching from persistence.

**Phase 1 — Fetch Index.** The service calls the external source's list endpoint, which returns a slim representation of each item (typically just an ID and a name). This is validated against a Pydantic model specific to the index response shape.

**Phase 2 — Fetch Detail.** For each item in the index, the service calls the detail endpoint to retrieve the full representation. This is validated against a separate Pydantic model for the detail response shape.

**Phase 3 — Convert and Upsert.** A pure function maps each external detail to an internal model instance. The orchestrator then upserts each converted record into the database, keyed by gold source ID.

The separation of index and detail schemas reflects the reality that list and detail endpoints often return different shapes. Keeping the conversion as a pure function (no IO, no session) makes it independently testable. The orchestrator does not commit — the caller (typically the route handler) owns the session lifecycle, which preserves all-or-nothing semantics: if any phase fails, nothing is persisted.

## External Schemas

Pydantic models for external API responses live under `app/schemas/external/`, separate from internal response schemas. Each external source has its own module with an index model (slim, for list responses) and a detail model (full, for single-item responses). These models describe the external contract, not the internal representation — the conversion function bridges the two.

## Gold Source Identity

Models that are synced from external systems inherit from `GoldSourceMixin`, which provides `gold_source_id` and `gold_source_type` fields with a composite unique constraint. This allows any synced record to be looked up by its external identity. Each model adds a composite index on these fields for query performance. The mixin provides a `get_by_gold_source` query method that returns a typed `Result[Option[T], DBError]`, consistent with the error handling pattern.

## Mock Services

External APIs are simulated by lightweight FastAPI applications under `mock-services/`. Each mock service loads fixture data from YAML files and serves it through endpoints that mirror the real external API structure (index and detail). Mock services are used both in local development (started via devenv) and in CI (started as background processes during test runs). They are intentionally simple and untested — their purpose is to provide deterministic, schema-valid responses for development and testing.

## Routes and Responses

Route handlers are thin. They call into service functions or query methods, receive typed Results, and convert them to HTTP responses. List endpoints support offset/limit pagination. Lookup endpoints return 404 when no record matches. Ingestion endpoints trigger the pipeline, commit on success, and return the count of ingested records or a 502 on failure.

Internal response schemas (under `app/schemas/`) define the shape of API responses. These are separate from both the database models and the external schemas — each layer has its own representation.
