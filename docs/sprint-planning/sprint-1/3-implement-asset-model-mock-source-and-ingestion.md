### Implement Asset Model, Mock Source and Ingestion

**Deps:** T2 — Base Model Mixins and Gold Source ID Pattern

Full vertical slice for the asset inventory external source.

- Create `app/models/asset.py` with an `Asset` model using `TimestampMixin` + `GoldSourceMixin` + `TagsMixin` + a composite index on `(gold_source_type, gold_source_id)`. Fields: id, name, description, tags, timestamps. No dedicated columns for protection_level or threat_classification.
- Generate an Alembic migration for the Asset table
- Create a FastAPI-based mock service under `mock-services/asset_inventory/` with YAML fixture data, serving a slim index endpoint (`GET /assets` returning id + name) and a full detail endpoint (`GET /assets/{id}`)
- Create `app/schemas/external/asset_inventory.py` with `AssetIndexItem` (id, name) and `AssetDetail` (id, name, description, tags) Pydantic models for the external API shape
- Create `app/routes/assets.py` with endpoints: list assets (paginated), get by ID, get by gold source, and trigger ingestion
- Create `app/services/asset_ingestion.py` with a three-phase ingestion pipeline:
  - `fetch_index` — fetches the asset list from the configured endpoint (URL from settings)
  - `fetch_detail` — fetches full detail for each index entry
  - `to_asset` — pure conversion from external detail to verdict Asset
  - `ingest_assets` orchestrator upserts Assets in a single transaction keyed by gold source ID (update if exists, create if not)
  - Rolls back entirely on any validation or persistence error (all-or-nothing)
  - Logs schema mismatch errors via Python logging (audit log integration added in T6)
- Create `tests/factories/asset.py` with an `AssetFactory`
- Unit tests with mocked HTTP (`respx`): valid response is ingested, invalid response is rejected with zero records persisted, re-ingestion upserts without creating duplicates, individual tests for `fetch_index`, `fetch_detail`, `to_asset`
- E2E tests (`tests/e2e/`) running against real services (postgres, mock service, verdict app): full ingestion workflow, retrieval by ID and gold source, re-ingestion idempotency, 404 handling
- CI integration via `enterTest` in `devenv.nix`: starts mock service and verdict app, runs E2E tests, cleans up

**Done:** Asset endpoints serve paginated lists, lookups by ID and gold source; three-phase ingestion pipeline fetches index and detail from FastAPI mock service and persists Assets; re-ingestion upserts by gold source ID without duplicates; invalid responses rejected with zero persisted records; E2E tests verify full round-trip through real services; CI runs both unit and E2E tests via `devenv test`.
