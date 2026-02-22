### Implement AuditLog Model

**Deps:** T2 — Base Model Mixins and Gold Source ID Pattern

- Create `app/models/audit_log.py` with an `AuditLog` model. Fields: id, operation (str), actor (str), actor_type (str enum: user/system/runner), timestamp (server-default), resource_type (str), resource_id (str, nullable), before_state (JSON, nullable), after_state (JSON, nullable), details (JSON, nullable).
- Generate an Alembic migration for the audit_log table
- Create `app/services/audit.py` with:
  - A `create_audit_entry(session, ...)` helper that persists an AuditLog record
  - Guard logic that refuses to update or delete existing AuditLog records (raises an error)
- Create `tests/factories/audit_log.py` with an `AuditLogFactory`
- Create tests: audit entries persist with all fields populated; attempting to update or delete an audit record via the service layer raises an error
- Retrofit T3 (`app/services/asset_ingestion.py`) and T4 (`app/services/cmdb_ingestion.py`) to call `create_audit_entry()` on schema mismatch errors instead of (or in addition to) Python logging

**Done:** Audit log entries persist with all fields; update/delete of audit records is refused by the service layer; T3/T4 ingestion services log schema mismatch errors as audit entries.
