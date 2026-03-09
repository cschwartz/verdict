# Error Handling

The backend uses typed Result and Option types instead of exceptions for recoverable errors.

## Result and Option

A `Result[T, E]` is either `Ok(value)` or `Err(error)`, where the error type is explicit in the signature. An `Option[T]` is either `Some(value)` or `Nothing()`, representing the presence or absence of a value. These compose naturally: a database lookup returns `Result[Option[T], DBError]`, meaning the operation itself can fail (Err) or succeed with either a found record (Ok(Some)) or no record (Ok(Nothing)).

## AppError Contract

All error types inherit from `AppError`, an abstract base class that enforces a two-level message contract. Each error exposes a `message` property (safe to return to clients) and a `detail` property (for internal logging only, may contain URLs, SQL statements, or driver messages). `__str__` returns `message`, so errors are safe by default anywhere they are converted to strings. Error types store their raw diagnostic data in fields and compute both properties from them.

Error types are domain-specific dataclasses defined in `app/errors.py`. They form unions that describe what can go wrong in each context: `IngestionError` covers fetch failures, schema validation errors, and database errors. Functions declare which error union they can produce, and callers handle each variant explicitly.

## Route Helpers

Routes bridge typed errors to HTTP responses via two helpers: `unwrap_or_raise` converts a `Result[T, E]` into either the unwrapped value or an HTTP error, while `unwrap_optional_or_raise` handles `Result[Option[T], E]` with an additional Nothing-to-404 mapping. Both log the error detail internally and return only the safe message to clients.

## Defence in Depth

The SQLAlchemy engine is configured with `hide_parameters=True`, which redacts SQL parameter values from exception messages and query logging at the driver level. This is a defence-in-depth measure alongside the `AppError` message/detail separation.

## Exceptions vs Results

Exceptions are reserved for programming errors (bugs) that should propagate and crash. Operational errors (network failures, missing records, schema mismatches) flow through Result types so they can be handled, composed, and tested without try/except.
