### Implement System Model, Mock Source and Ingestion

**Deps:** T2 — Base Model Mixins and Gold Source ID Pattern, T3 — Implement Asset Model, Mock Source and Ingestion

Full vertical slice for the CMDB external source.

- Create `app/models/system.py` with a `System` model using `TimestampMixin` + `GoldSourceMixin` + `TagsMixin` + a composite index via `GoldSourceMixin.gold_source_index("system")`. Fields: id, hostname, primary_fqdn, `asset_id` FK to Asset (nullable), tags, metadata (JSON), timestamps.
- Generate an Alembic migration for the System table
- Create a FastAPI-based mock service under `mock-services/cmdb/` with YAML fixture data, serving a slim index endpoint (`GET /systems` returning id + hostname) and a full detail endpoint (`GET /systems/{id}`)
- Create `app/schemas/external/cmdb.py` with `SystemIndexItem` and `SystemDetail` Pydantic models for the external API shape
- Create `app/routes/systems.py` with endpoints: list systems (paginated), get by ID, get by gold source, and trigger ingestion
- Create `app/services/cmdb_ingestion.py` with a three-phase ingestion pipeline:
  - `fetch_index` — fetches the system list from the configured CMDB endpoint
  - `fetch_detail` — fetches full detail for each index entry
  - `to_system` — pure conversion from external detail to verdict System; resolves `asset_gold_source_id` to an internal Asset FK via `get_by_gold_source()`
  - `ingest_systems` orchestrator upserts Systems in a single transaction keyed by gold source ID
  - Rejects the entire payload if any asset reference is unresolvable (all-or-nothing)
  - Logs schema mismatch errors via Python logging (audit log integration added in T6)
- Create `tests/factories/system.py` with a `SystemFactory`
- Unit tests with mocked HTTP (`respx`): valid response persists Systems linked to their Assets, unresolvable asset reference rejects entire payload with zero persisted records, upsert works on re-ingestion, individual tests for `fetch_index`, `fetch_detail`, `to_system`
- E2E tests running against real services: full ingestion workflow, retrieval by ID and gold source, re-ingestion idempotency

**Done:** System endpoints serve paginated lists, lookups by ID and gold source; three-phase ingestion pipeline fetches index and detail from FastAPI mock service and persists Systems; each System is linked to its Asset via resolved gold source ID; unresolvable asset reference rejects the entire payload with zero persisted records; upsert works on re-ingestion; E2E tests verify full round-trip through real services.
