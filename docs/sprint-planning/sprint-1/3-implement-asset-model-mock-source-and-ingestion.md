### Implement Asset Model, Mock Source and Ingestion

**Deps:** T2 — Base Model Mixins and Gold Source ID Pattern

Full vertical slice for the asset inventory external source.

- Create `app/models/asset.py` with an `Asset` model using `TimestampMixin` + `GoldSourceMixin` + a `tags` JSON column. Fields: id, name, description, tags, timestamps. No dedicated columns for protection_level or threat_classification.
- Generate an Alembic migration for the Asset table
- Create `mock-services/specs/asset-inventory.yaml` — an OpenAPI 3.x spec with a GET endpoint that returns a list of assets, each with an external ID, name, description, and hierarchical tags. Include realistic `examples`.
- Create `app/schemas/asset.py` with a Pydantic response model matching the asset inventory API response shape
- Create `app/services/asset_ingestion.py` with an ingestion service that:
  - Fetches from the configured asset inventory endpoint (URL from settings)
  - Validates the response against the Pydantic schema
  - Upserts Assets in a single transaction keyed by gold source ID (update if exists, create if not)
  - Rolls back entirely on any validation or persistence error (all-or-nothing)
  - Logs schema mismatch errors via Python logging (audit log integration added in T6)
- Create `tests/factories/asset.py` with an `AssetFactory`
- Create tests with mocked HTTP (e.g. `respx` or `unittest.mock`): valid response is ingested, invalid response is rejected with zero records persisted, re-ingestion upserts without creating duplicates

**Done:** Ingestion service fetches from mock endpoint and persists Assets; re-ingestion upserts by gold source ID without duplicates; invalid response is rejected with zero persisted records; `prism mock mock-services/specs/asset-inventory.yaml` serves valid example data.
