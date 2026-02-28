### Implement OSCAL Mock Source and Ingestion

**Deps:** T6 — Audit Log Model, T11 — Statement Model

- Create a FastAPI-based mock service under `mock-services/grc_oscal/` with YAML fixture data, serving:
  - `GET /policies` — index returning policy IDs
  - `GET /policies/{id}` — policy detail including its standard IDs
  - `GET /standards/{id}` — standard detail including its statement IDs
  - `GET /statements/{id}` — statement detail
- Create `app/schemas/external/grc_oscal.py` with index and detail Pydantic models for each level: `PolicyIndexItem`, `PolicyDetail` (includes standard IDs), `StandardDetail` (includes statement IDs), `StatementDetail`
- Create `app/routes/oscal.py` with an endpoint to trigger ingestion
- Create `app/services/oscal_ingestion.py` with a three-phase ingestion pipeline that walks the hierarchy:
  - `fetch_index` — fetches the policy list from the configured GRC/OSCAL endpoint
  - `fetch_policy_detail`, `fetch_standard_detail`, `fetch_statement_detail` — fetches full detail at each level, following child IDs down the tree
  - `to_policy`, `to_standard`, `to_statement` — pure conversions from external detail to verdict models
  - `ingest_policies` orchestrator upserts the full Policy → Standard → Statement hierarchy in a single transaction keyed by gold source IDs
  - On re-ingestion, replaces the hierarchy for a given policy (cascade handles orphan cleanup)
  - Rolls back entirely on any validation or persistence error (all-or-nothing)
  - Logs schema mismatch errors to the audit log via `create_audit_entry()`
- Unit tests with mocked HTTP (`respx`): valid nested response persists full hierarchy, invalid response rejected with zero persisted records, re-ingestion replaces existing hierarchy, schema mismatch creates an audit log entry, individual tests for fetch and conversion functions
- E2E tests running against real services: full ingestion workflow, hierarchy retrieval via policy/standard/statement endpoints

**Done:** Ingestion endpoint triggers three-phase pipeline that walks the OSCAL hierarchy and persists full Policy → Standard → Statement tree; re-ingestion replaces the hierarchy for a given policy; invalid response rejected with zero persisted records; schema mismatch logged to audit log; E2E tests verify full round-trip through real services.
