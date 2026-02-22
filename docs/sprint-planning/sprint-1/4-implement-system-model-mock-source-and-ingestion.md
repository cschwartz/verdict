Full vertical slice for the CMDB external source.

- Create `app/models/system.py` with a `System` model using `TimestampMixin` + `GoldSourceMixin` + a `tags` JSON column. Fields: id, hostname, primary_fqdn, `asset_id` FK to Asset (nullable), tags, metadata (JSON), timestamps.
- Generate an Alembic migration for the System table
- Create `mock-services/specs/cmdb.yaml` — an OpenAPI 3.x spec with a GET endpoint returning a list of systems, each with an external ID, hostname, primary_fqdn, tags, and an `asset_gold_source_id` string for linking to an asset. Include realistic `examples`.
- Create `app/schemas/cmdb.py` with a Pydantic response model matching the CMDB API response shape
- Create `app/services/cmdb_ingestion.py` with an ingestion service that:
  - Fetches from the configured CMDB endpoint
  - Validates the response against the Pydantic schema
  - For each system, resolves `asset_gold_source_id` to an internal Asset FK via `get_by_gold_source()`
  - Upserts Systems in a single transaction keyed by gold source ID
  - Rejects the entire payload if any asset reference is unresolvable (all-or-nothing)
  - Logs schema mismatch errors via Python logging (audit log integration added in T6)
- Create `tests/factories/system.py` with a `SystemFactory`
- Create tests: valid response persists Systems linked to their Assets, unresolvable asset reference rejects entire payload with zero persisted records, upsert works on re-ingestion

**Done:** Ingestion service fetches from mock CMDB and persists Systems; each System is linked to its Asset via resolved gold source ID; unresolvable asset reference rejects the entire payload with zero persisted records; upsert works on re-ingestion.
