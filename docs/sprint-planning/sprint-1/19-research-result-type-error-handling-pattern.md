### Research Result Type Error Handling Pattern

**Deps:** None

Research ticket — produces a written recommendation, no code.

The project currently lets database and operational errors propagate as exceptions. As the service layer grows (ingestion services, `get_by_gold_source`, audit log writes), we need a consistent error handling pattern that makes failure explicit in return types rather than relying on implicit exception propagation. This ticket evaluates Rust-like `Result` / functional `Either` approaches for Python.

- Survey available Python libraries and patterns:
  - [returns](https://github.com/dry-python/returns) (`Result`, `Maybe`, `IO` containers with do-notation)
  - [result](https://github.com/rustedpy/result) (lightweight Rust-style `Ok`/`Err`)
  - [poltergeist](https://github.com/alexandermalyga/poltergeist) (minimal `Result` type)
  - Rolling our own minimal `Result[T, E]` type
  - Plain union return types (`T | ErrorType`) without a library
- Evaluate each candidate against these criteria:
  - **API ergonomics:** How natural is it to use in Python? Does it compose well with existing patterns (SQLModel sessions, FastAPI dependencies)?
  - **Type checker support:** Does mypy correctly narrow `Ok` vs `Err` branches? Does it work under `--strict`?
  - **Python 3.14+ compatibility:** Must work on the project's target runtime
  - **Library maturity:** Commit activity, maintainers, test coverage, adoption
  - **Overhead:** Does it add meaningful complexity for contributors unfamiliar with the pattern?
  - **Scope fit:** We need this primarily for service-layer functions (queries, ingestion, writes) — not for every function in the codebase. Does the candidate work well when applied selectively?
  - **Integration with SQLAlchemy/SQLModel:** Can `IntegrityError`, `NoResultFound`, and connection errors be cleanly captured into the Result type?
- Evaluate the tradeoffs vs. staying with exceptions:
  - Where do explicit Result types add clarity (e.g., `get_by_gold_source` returning `Result[T, NotFound | DBError]`)?
  - Where are exceptions still the right choice (e.g., unrecoverable infrastructure failures)?
  - What is the boundary — which layers use Result types and which use exceptions?
- Write a recommendation document to `docs/decisions/` with findings and a clear recommendation

**Done:** A written recommendation exists in `docs/decisions/` that evaluates at least three approaches, states a clear recommendation (adopt library X, roll our own, or stay with exceptions), and defines the boundary where Result types should be used in the codebase.
