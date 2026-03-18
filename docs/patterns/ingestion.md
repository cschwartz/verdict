# Ingestion

## Single-Source Pipeline

External data is ingested through a three-phase pipeline that separates fetching from persistence.

**Phase 1 — Fetch Index.** The service calls the external source's list endpoint, which returns a slim representation of each item (typically just an ID and a name). This is validated against a Pydantic model specific to the index response shape.

**Phase 2 — Fetch Detail.** For each item in the index, the service calls the detail endpoint to retrieve the full representation. This is validated against a separate Pydantic model for the detail response shape.

Both fetch phases go through the `fetch_json` helper (`app/http.py`), which handles HTTP errors uniformly: transport/status failures become `FetchError` (with the URL), and Pydantic parse failures become `RemoteValidationError` (a URL-aware `ValidationError` subclass). Services declare their source error type as `FetchError | RemoteValidationError`.

**Phase 3 — Convert and Upsert.** A pure function maps each external detail to an `XCreate` model instance. The orchestrator then upserts each converted record into the database, keyed by gold source ID (the record's unique identifier in the external system — see [Gold Source Identity](models.md#gold-source-identity)), and returns `XPublic` instances via `model_validate` after flush.

The separation of index and detail schemas reflects the reality that list and detail endpoints often return different shapes. Keeping the conversion as a pure function (no IO, no session) makes it independently testable. The orchestrator does not commit — the caller (typically the route handler) owns the session lifecycle, which preserves all-or-nothing semantics: if any phase fails, nothing is persisted.

## Cross-Source Orchestration

When multiple sources need to be ingested atomically, a global ingestion endpoint (`POST /ingest`) runs each source's pipeline in sequence within a single session. It commits only if all sources succeed. If any source fails, the session is rolled back and nothing is persisted.

Sources that reference records from other sources (e.g., systems referencing assets) resolve those references by gold source ID during their pipeline. If a referenced record cannot be found, the entire source's ingestion is rejected.

The upsert helpers (`upsert_by_gold_source`, `_upsert_permission`) use a select-then-insert pattern and only catch `OperationalError` on flush. `IntegrityError` from a concurrent insert is deliberately not handled: all ingestion and config-sync callers are single-threaded batch operations, so the race cannot occur. If concurrent callers are ever introduced, add `IntegrityError` handling at the flush site.

## Link Resolution and Syncing

For N:M relationships that cross source boundaries, the ingestion pipeline resolves external IDs to internal IDs using `get_by_gold_source`. After upserting the parent record, a diff-based sync step compares the desired set of linked IDs against the current set in the database, then issues INSERT and DELETE statements against the join table to reconcile the difference. This ensures re-ingestion is idempotent — links are added or removed to match the source of truth without duplicating or orphaning entries.

## External Schemas

Pydantic models for external API responses live under `app/schemas/external/`, separate from internal response schemas. Each external source has its own module with an index model (slim, for list responses) and a detail model (full, for single-item responses). These models describe the external contract, not the internal representation — the conversion function bridges the two.
