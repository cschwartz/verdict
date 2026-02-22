### Implement OSCAL Mock Source and Ingestion

**Deps:** T6 — AuditLog Model, T11 — Statement Model

- Create `mock-services/specs/grc-oscal.yaml` — an OpenAPI 3.x spec with a GET endpoint returning a nested structure of policies, each containing standards, each containing statements. Include realistic `examples` with OSCAL-style identifiers.
- Create `app/schemas/oscal.py` with nested Pydantic response models matching the GRC/OSCAL API response shape (policies → standards → statements)
- Create `app/services/oscal_ingestion.py` with an ingestion service that:
  - Fetches from the configured GRC/OSCAL endpoint
  - Validates the response against the Pydantic schema
  - Upserts the full Policy → Standard → Statement hierarchy in a single transaction keyed by gold source IDs
  - On re-ingestion, replaces the hierarchy for a given policy (cascade handles orphan cleanup)
  - Rolls back entirely on any validation or persistence error (all-or-nothing)
  - Logs schema mismatch errors to the audit log via `create_audit_entry()`
- Create tests with mocked HTTP: valid nested response persists full hierarchy, invalid response rejected with zero persisted records, re-ingestion replaces existing hierarchy, schema mismatch creates an audit log entry

**Done:** Ingestion service fetches nested OSCAL payload and persists full Policy → Standard → Statement hierarchy; re-ingestion replaces the hierarchy for a given policy; invalid response rejected with zero persisted records; schema mismatch logged to audit log.
