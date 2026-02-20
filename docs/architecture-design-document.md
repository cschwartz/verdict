title: Verdict: GRC-Engineering Platform Architecture Document

# Verdict: GRC-Engineering Platform Architecture Document

## 1. Executive Summary

**Verdict** is a compliance automation and evidence collection system that bridges three layers of abstraction:

- **Governance Layer** (OSCAL policies and standards)
- **Business Architecture** (IT-asset inventory with ITIL-level abstractions)
- **Technical Layer** (CMDB with concrete systems, hostnames, IPs, technical metadata)

Verdict automatically discovers which compliance checks apply to which systems (via tag-based mappings), executes those checks through pluggable execution backends, collects evidence of compliance in a tamper-proof manner, and provides queryable APIs for consumption by compliance tools, risk management systems, and business intelligence platforms.

## 2. System Architecture Overview

```
┌────────────────────────────────────────────────────────────────────────┐
│                      EXTERNAL DATA SOURCES                             │
├──────────────┬──────────────────────┬──────────────────────────────────┤
│   GRC Tool   │    Asset Inventory   │               CMDB               │
│    (OSCAL)   │  (ITIL abstractions) │        (Technical Systems)       │
└──────┬───────┴──────────┬───────────┴──────────┬───────────────────────┘
       │                  │                      │
       ▼                  ▼                      ▼
┌────────────────────────────────────────────────────────────────────────┐
│                    INGESTION & MAPPING LAYER                           │
├────────────────────────────────────────────────────────────────────────┤
│ - OSCAL Ingestion        - Asset Inventory Sync   - CMDB Sync          │
│ - Policy/Standard Store  - Asset-System Mappings  - Tag Normalization  │
└─────────────────────────────────┬──────────────────────────────────────┘
                                  │
                                  ▼
┌────────────────────────────────────────────────────────────────────────┐
│                    CHECK LIBRARY & TAG MAPPING                         │
├────────────────────────────────────────────────────────────────────────┤
│ - Plugin Registry       - Tag Mapping Config     - Check Metadata      │
│ - Check Definitions       (YAML: plugin → user)  - Applicability Rules │
└─────────────────────────────────┬──────────────────────────────────────┘
                                  │
                ┌─────────────────┼──────────────────┐
                │                 │                  │
                ▼                 ▼                  ▼
       ┌────────────────┐ ┌────────────────┐ ┌────────────────┐
       │  ORCHESTRATOR  │ │ TASK MANAGER   │ │  DISPATCHER    │
       ├────────────────┤ ├────────────────┤ ├────────────────┤
       │  Check Appli-  │ │ Scheduling,    │ │  Route to      │
       │  cability      │ | Retry Logic    │ │  Runners       │
       └────────┬───────┘ └───────┬────────┘ └────────┬───────┘
                │                 │                   │
                └─────────────────┼───────────────────┘
                                  │
                                  │
                ┌─────────────────┼───────────────────┐
                │                 │                   │
                ▼                 ▼                   ▼
       ┌────────────────┐ ┌────────────────┐ ┌────────────────┐
       │  AGENTS        │ │ PYTHON RUNNER  │ │ OTHER          │
       ├────────────────┤ ├────────────────┤ ├────────────────┤
       │ Check system   │ │ Check compli-  │ │                │
       │ configuration  │ | ance via serv- │ │                │
       │ by local agent │ │ ices           │ │                |
       └────────┬───────┘ └───────┬────────┘ └────────┬───────┘
                │                 │                   │
                └─────────────────┼───────────────────┘
                                  │
                                  │
                                  ▼
┌────────────────────────────────────────────────────────────────────────┐
│               EVIDENCE COLLECTION & FORMATTING                         │
├────────────────────────────────────────────────────────────────────────┤
│ - Evidence Model Formatting (pass/fail, timestamp, details, metadata)  │
│ - Cryptographic Signing                                                │
│ - Failure & Retry Tracking (as evidence)                               │
└─────────────────────────────────┬──────────────────────────────────────┘
                                  │
                                  ▼
┌────────────────────────────────────────────────────────────────────────┐
│              EVIDENCE STORAGE & AUDIT TRAIL                            │
├────────────────────────────────────────────────────────────────────────┤
│ - Tamper-Proof Store (cryptographically signed)                        │
│ - Append-Only (with WORM storage plugin as future option)              │
│ - Full Audit Trail of all operations                                   │
│ - Retention: Years                                                     │
└───────────────────────────────────┬────────────────────────────────────┘
                ┌───────────────────┼─────────────────┐
                │                   │                 │
                ▼                   ▼                 ▼
       ┌────────────────┐ ┌────────────────┐ ┌────────────────┐
       │ COMPLIANCE     │ │ RISK MGMT      │ │ REPORTING      │
       ├────────────────┤ ├────────────────┤ ├────────────────┤
       │ Push evidence  │ │ Push evidence  │ │ Provide data   │
       │ to REST API    │ | ance via serv- │ │ for pull via   │
       │                │ │                │ │ REST API       |
       └────────────────┘ └────────────────┘ └────────────────┘
```

## 3. Core Components

### 3.1 Ingestion & Mapping Layer

**Purpose:** Ingest and normalize data from three external sources; establish connections between policy, assets, and technical systems.

**Ingestion Strategy (Sprint 1):**
- Mock external sources with REST endpoints and predefined schemas
- All-or-nothing semantics: entire asset/OSCAL/CMDB query succeeds or fails atomically
- Schema mismatch = fatal error; logged as evidence entry (operational visibility)
- No partial updates; validation before commit
- Refresh frequency: Configured per entity type

**Subcomponents:**

- **OSCAL Ingester**
  - Mocks or pulls from OSCAL/GRC tool REST endpoint
  - Parses OSCAL documents
  - Extracts policies, standards, statements, and requirements
  - Stores in normalized internal representation
  - Gold source reference: OSCAL policy/control ID

- **Asset Inventory Sync**
  - Mocks or pulls from asset inventory REST endpoint
  - Captures IT-assets with business context (protection requirements, threat classifications, etc.)
  - Associates hierarchical tags (e.g., `protection-level.high`, `business-unit.finance`)
  - Gold source reference: external asset inventory ID

- **CMDB Sync**
  - Mocks or pulls from CMDB REST endpoint
  - Captures concrete technical systems (hostnames, FQDNs, IPs, etc.)
  - Associates technical tags (e.g., `os.linux.ubuntu-22.04`, `role.database`, `cloud-provider.aws`)
  - Maps systems to assets via pre-configured hierarchical tag-based relationships
  - Refresh frequency: Configured per entity type

**Implementation Notes:**
- Webhook-based push from external sources deferred to post-PoC

### 3.2 Check Library & Tag Mapping

**Purpose:** Define what checks exist, which systems they apply to, and how plugin tags map to user domain tags.

**Subcomponents:**

- **Plugin Registry**
  - Version-controlled directory (git-based)
  - Plugins can be cloned, submoduled, or copied into this directory
  - Auto-discovery of plugins via metadata files

- **Check Definitions**
  - Each plugin declares:
    - Check name and description
    - Execution model (which runner: inspec, python, agent-based, remote exec, etc.)
    - Plugin-specific tags (the vocabulary of this check)
    - Metadata (author, version, etc.)

- **Tag Mapping Configuration (YAML)**
  - Centralized mapping: `plugin.tag_X` → `user.domain_tag_Y`
  - User-specific domain tags span:
    - OSCAL policies/standards
    - Asset inventory tags
    - CMDB technical tags
  - Enables matching checks to systems despite tag nomenclature differences
  - Version-controlled in config repo
  - GRC Engineer responsible for correctness; Git commit log and CI/CD code review enforce approval (benefit of repo-based approach)

- **Applicability Rules & Tag DSL**
  - Tag hierarchy support: `linux.ubuntu-22.04` hierarchically allows matching on `linux`
  - Conjunction support (AND/OR logic): `{os.linux AND role.database}` or similar
  - DSL to be defined in Sprint 2 for complex conjunctions
  - Applicability derived from tag mappings and policy statements, determines: "This check applies to systems tagged with {X, Y, Z}"

**Implementation Notes:**
- External repo management, vendoring, CI/CD integration = GRC Engineer responsibility (outside platform scope)
- Tag mapping mismatches are GRC Engineer responsibility (enforced via Git review or pipeline quality gates)

### 3.3 Orchestrator, Task Manager & Dispatcher

**Purpose:** Determine which checks apply to which systems using applicability rules, schedule execution, manage retries, and route work to appropriate runners.

**Subcomponents:**

- **Orchestrator (Check Applicability)**
  - At startup: evaluates all (policy statement × system) pairs
  - On config sync: re-evaluates applicability (checks, mappings may have changed)
  - On external data refresh: re-evaluates applicability (asset tags, system tags may have changed)
  - On-demand: optional; may be added in post-PoC version
  - Uses tag mappings and applicability rules to determine applicable checks
  - Builds applicability matrix: (policy, standard, statement, check, asset, system) → Boolean
  - Deduplicates overlapping checks
  - **Note:** Check applicability is computed from a snapshot of config state at execution time. If external data (CMDB, asset inventory) changes, applicability may change. Historical evidence retains temporal reference to policies/statements at time of collection; audit logs capture timing of external data changes. **Post-PoC improvement:** Webhooks/notifications for external data changes.

- **Task Manager**
  - Schedules check execution using cron-like format strings (e.g., `0 2 * * *` for daily 2 AM)
  - Scheduling is defined per-check in platform config (not check config; however defaults may be provided by the check)
  - Implements retry logic with atomic tracking
  - Tracks task state (pending, running, success, failed, retry)
  - Logs all retry attempts as evidence
  - Pauses pending checks if config sync is in progress (ensures consistency)

- **Dispatcher**
  - Routes each task to the appropriate runner based on check's execution model
  - Manages runner availability via heartbeat monitoring
  - Uses round-robin selection for multiple runners of same type
  - Reuses existing task runner framework; does not re-implement

### 3.4 Execution Backends (Runners)

**Purpose:** Execute checks via different mechanisms; collect raw check output.

**Execution Models (all supported):**

1. **Agent-Based Runners**
   - **XDR-style (on-system agents):** Agents run on managed systems, pull tasks, execute locally
   - **Centralized (osquery-style wrapper):** Central agent queries multiple systems
   - **Others TBD:** Docker, Kubernetes, custom integrations

2. **Python SDK Runner**
   - Loads user-written Python plugins
   - Plugins import a system-provided library for querying resources
   - Executes plugin code; captures returned evidence
   - Example uses: SIEM Query, Config Management, API-Based Services (e.g., Cloud Provider, JIRA, ServiceNow)

3. **Inspec Runner**
   - Executes inspec profiles
   - Parses inspec output (JSON)

4. **Agent-Less Remote Execution Runners**
   - SSH/WinRM to target systems
   - Execute scripts or commands; capture output

Each runner is responsible for:
- Executing the check
- Capturing all output (pass/fail, details, metadata)
- Handling failures gracefully
- Returning cryptographically signed evidence in a standardized format (schema-validated)
- Reporting public key on startup and after key rotation (for platform storage and verification)

**Runner Lifecycle (PoC Model):**
- **Startup:** Runner registers with platform, reports:
  - Runner type and version
  - Supported check types
  - Public key (for evidence signing verification)
  - Service account credentials (API key or mTLS certificate)
- **Heartbeat:** Runner sends periodic heartbeat to platform (dispatcher monitors availability)
- **Task Assignment:** Dispatcher uses round-robin to assign tasks to available runners
- **Execution & Signing:** Runner executes check, signs evidence (private key on runner filesystem), submits to platform
- **Key Rotation:** Runner can rotate keys; reports new public key to platform on rotation
- **Note:** Platform reuses existing task runner framework (e.g., Celery) for management; does not re-implement queue/dispatch logic (Sprint 2 assignment)


### 3.5 Evidence Collection & Formatting

**Purpose:** Standardize the output from all execution backends into a common evidence model; evidence collected at check/system granularity.

**Evidence Granularity & Scope:**
- Evidence is collected and stored at the **check/CMDB item level** — atomic results from running a single check against a single system
- **Out of Scope:** Quantitative rollup (e.g., "system is 85% compliant"), remediation status, control owner assignment, risk acceptance/waivers
- These higher-level aggregations are the responsibility of:
  - The downstream **GRC tool** (risk management, remediation tracking), or
  - A separate **aggregation service** between Verdict and the GRC tool
- **Verdict's role:** Provide raw evidence; let downstream systems compute risk posture / compliance state

**Evidence Model (to be finalized in Sprint 3):**

Each piece of evidence should capture:
- **Check Identification:** (policy, standard, statement, check_id)
- **System Identification:** (asset, system, hostname, IP, gold-source-id)
- **Execution Metadata:**
  - Timestamp of execution
  - Runner type used
  - Execution duration
  - Execution status (success, failure, error)
- **Result Data:**
  - Pass/Fail status
  - Detailed output from the check
  - Raw evidence artifacts (logs, configurations, scan results, etc.)
- **Retry Information (if applicable):**
  - Attempt number
  - Previous attempt results
  - Time between retries
- **Cryptographic Signature**
  - Hash of evidence (SHA-256 or stronger)
  - Digital signature (runner identity, timestamp)
  - Public key ID/version (for verification with key rotation)

**Evidence Format & Normalization:**
- **Primary Format:** JSON (API/storage)
- **Schema:** Standardized but extensible evidence schema
- **Schema Mismatch:** Treated as fatal error; logged as evidence and blocks storage
- **Extensibility:** Schema includes fields for runner-specific metadata

**Check Failure & Error Handling:**
- If a check fails to run (runner crash, timeout, schema mismatch, etc.), the failure is logged as evidence
- Failures are atomic (all-or-nothing: evidence fully recorded or transaction rolls back; no partial states)
- Critical failures (storage unavailable, runner framework issues) trigger operational alerts


### 3.6 Evidence Storage & Audit Trail

**Purpose:** Store evidence in a tamper-proof, auditable manner; maintain audit trail of operational events.

**Requirements:**

- **Cryptographic Signing:** All evidence records signed by runner before submission; verified before storage
- **Append-Only:** No modification of existing records
- **Audit Trail:** Operational events logged (evidence submission, config changes)
- **Tamper Detection:** Ability to verify integrity of stored records (signature validation)
- **Future: WORM Storage Plugin** — Deferred for PoC; consider as pluggable storage backend; fallback: yearly export to WORM storage

**Audit Scope (PoC):**
- **Logged:** Evidence submission events, config sync operations
- **Not logged (for volume management):** Read/query operations, all auth/authz decisions

**Storage Strategy (PoC):**
- **PostgreSQL** (primary data store)
- Cryptographic hash chain (each evidence record includes hash of previous record) per system (i.e., asset / cmdb entry)
- Separate audit log table for operational events
- Indexes on gold-source IDs (for fast lookup by external system references)
- Deferred: Partitioning (by time, asset / cmdb entry), retention policy, archival/vacuum strategy


### 3.7 Query API

**Purpose:** Provide programmatic access to stored evidence for downstream systems and BI platforms.

**API Scope (PoC):**
- **Primary Goal:** Queryable access to raw evidence; GRC tool and downstream systems consume via API to compute higher-level insights

- **REST API** for querying evidence by:
  - Time range
  - Policy/standard/statement
  - Asset/system (by internal ID or gold-source ID)
  - Check ID
  - Compliance status (pass/fail/error)
  - Combinations thereof (e.g., "all evidence for asset X failing standard Y")

- **Data Lake Integration:** BI tools can pull evidence directly from the query API to populate data lakes for advanced analysis and reporting

- **Basic Aggregation Endpoints** (for GRC engineer inspection; not for automated decision-making):
  - Compliance status summary (# policies met, # systems compliant, etc.)
  - Trend analysis (compliance over time)
  - Gap analysis (which checks failing, which assets non-compliant)

- **Field-Level Evidence Access Control:** Via field-level permissions (e.g., hide sensitive details); future versions may support check/asset type permissions

**Out of Scope:**
- Quantitative rollup, remediation status, risk scoring (downstream GRC tool responsibility)

**No UI:** API-first; visualization and advanced reporting deferred to BI tools and data lake infrastructure


### 3.8 Authentication & Authorization

**Purpose:** Control access to the system and evidence; ensure auditability of all operations.

**Permission Model:**

All platform endpoints follow a consistent permission schema:
- **Format:** `resource:subresource:action` (aligned with URL path structure)
- **Examples:**
  - `evidence:by-asset-id:read` (access `/evidence/by-asset-id/*`)
  - `check:create` (POST to create new check)
  - `config:sync` (trigger configuration repository sync)
- **Flexibility:** Permissions can be granular (specific subresources) or broad (all actions on a resource)
- **Assignment:** Permissions are assigned to roles; roles are assigned to users
- **Future Evolution:** Permission-to-role mapping can be changed without modifying endpoint logic

**User Types & Roles:**

- **GRC Engineer** (human, internal)
  - Operates and maintains Verdict
  - Integrates checks from Policy Engineers into the system's configuration repository
  - Manages tag mappings, check applicability rules, and system configuration
  - Manages user roles and permissions
  - Runs manual checks on-demand
  - Accesses evidence for investigation and incident response
  - Provides basic aggregated evidence views for compliance inspection
  - Default permissions: `config:sync`, `mapping:*`, `check:get`, `evidence:*`, `task:create`, `user:manage`

- **Policy Engineer** (human, external)
  - Authors and maintains checks and check definitions (outside platform)
  - Provides checks to GRC Engineer via version-controlled configuration repository
  - Does not directly interact with Verdict; integration is config-driven
  - Responsible for check maintenance and updates

- **Auditor** (human, internal)
  - Reads all evidence; cannot modify or run tasks
  - Conducts compliance reviews and evidence inspections
  - No access to system configuration or operational controls
  - Default permissions: `evidence:read`, `check:get`, `mapping:get`

- **Data Consumer / BI Tool** (machines)
  - Query API access to pull evidence for data lake and reporting
  - No write access; limited to read queries for aggregation/analysis
  - Default permissions: `evidence:read`, `evidence:by-asset-id:read`, `evidence:by-policy:read` (and similar aggregation endpoints)

- **System Actors** (machines - agents, task runners)
  - Task runners (inspec, python, agents) authenticate to system
  - Agents authenticate to system to receive tasks and submit evidence
  - Remote executors (SSH, API runners) authenticate to target systems
  - Service account permissions: `task:get`, `evidence:create`, `system:get`

**Authentication Methods:**

- **Humans (API):** Traditional API keys / secrets (short-lived tokens preferred)
- **Agents/Runners/BI Tools:**
  - API keys / secrets (service accounts)
  - **Certificate-based auth (preferred for cloud):** mTLS with client certificates
  - Support for both simultaneously
- **Secret Management:** Integrate with existing tools (e.g., Vault) for credential storage and rotation

**Auditability:**

- Who ran which check, when, and results (tracked in evidence)
- Tamper-evident design (cryptographic signatures on evidence prevent retroactive modification)
- Audit log tracks evidence submission and config change events
- (Note: Auth/authz decision logging deferred; can be added post-PoC)

### 3.9 Configuration Management & Repository Sync

**Purpose:** Enable GRC Engineers to integrate externally-maintained checks and configurations into the running platform.

**Configuration Repository:**
- Version-controlled (Git-based), owned by GRC Engineers
- Contains: Tag mappings, check references/vendored checks, system configuration
- Checks themselves are external artifacts (maintained by Policy Engineers in separate repos)
- Can be vendored via submodules, git submodules, or copied

**Sync Mechanism:**
- **Endpoint:** GRC Engineer triggers a sync operation, specifying a repo reference (commit hash, tag, branch)
- **Validation:** Platform validates schema correctness and reference integrity (checks exist, dependencies resolve)
- **External Repos:** Platform does not manage external check repositories; that is the GRC Engineer's responsibility (may be handled via CI/CD pipelines)
- **Permissions:** Requires `config:sync` permission; assigned by default to GRC Engineer role
- **Audit Trail:** Sync operation logged with repo reference, timestamp, and GRC Engineer identity

**Scope:**
- Tag mappings are read from config repo and loaded into platform
- Check applicability rules are computed at runtime from mappings + cached entity
- External entity data (policies, assets, systems) remain in platform DB and are refreshed on configured schedule
- Evidence stays in platform DB; not version-controlled

### 4.1 Core Entities

**Data Storage & Refresh Model:**

The platform stores and manages data from multiple sources with different refresh cadences:

- **Configuration Repository (Git-based)**
  - **Stored Here:** Tag mappings (enterprise's current security state for evidence collection), Checks, overall Verdict configuration
  - **Managed by:** GRC Engineer
  - **Refresh:** On-demand via `config:sync` endpoint

- **Platform Database (PostgreSQL)**
  - **External Entity Data (Cached):**
    - Policies, standards, statements (from OSCAL/GRC tool)
    - Assets and IT-asset inventory data
    - CMDB systems and technical metadata
    - Refresh frequency: Configured per entity type (e.g., hourly, daily)
  - **Computed Data (Runtime):**
    - Check applicability rules (derived from tag mappings + cached entity data)
    - Regenerated on config sync or on-demand
  - **Primary Data:**
    - Evidence (collected from check execution, immutable, append-only)
    - Audit trail (all operations)
    - User accounts, roles, permissions
  - **External References:**
    - Gold source IDs linking internal entities to external systems


#### Core Entity Definitions:

**Policy/Standard/Statement**
- Policy ID, name, description
- Standard (links to policy)
- Statement (links to standard)
- OSCAL reference data
- Storage: Platform DB (cached from GRC tool)
- Gold source reference: OSCAL policy/control ID

**Asset**
- Asset ID (internal system ID), name, description
- Gold Source ID (reference ID from external asset inventory)
- Hierarchical tags (from asset inventory), such as protection requirements, threat classifications
- Links to systems (in CMDB)
- Storage: Platform DB (cached from asset inventory)
- Refresh: Configured frequency (e.g., hourly)

**System (CMDB)**
- System ID (internal system ID), hostname, FQDN, IP address
- Gold Source ID (reference ID from external CMDB)
- Technical tags (OS, role, cloud provider, etc.)
- Links to asset
- Configuration metadata
- Storage: Platform DB (cached from CMDB)
- Refresh: Configured frequency (e.g., hourly)

**Check**
- Check ID, name, description
- Runner type (inspec, python, agent, api, etc.)
- Plugin metadata (author, version)
- Plugin-specific tags
- Storage: Platform DB (loaded from config repo on sync)
- Source: Configuration repository (checked and validated on sync)

**Tag Mapping**
- Plugin tag → User domain tag
- Hierarchical relationships
- Storage: Platform DB (loaded from config repo on sync)
- Source: Configuration repository (version-controlled, updated on `config:sync`)

**Check Applicability**
- (Policy, Standard, Statement, Check, Asset, System) → Boolean
- Derived from tag mappings at orchestration time
- Storage: Not persisted; computed at runtime
- Recomputed on: Config sync, on-demand orchestrator rebuild

**Evidence**
- Evidence ID, timestamp, check ID, system ID, asset ID, policy/standard/statement
- Execution metadata (runner, duration, status)
- Result data (pass/fail, details, artifacts)
- Cryptographic signature
- Retry information (if applicable)
- Storage: Platform DB (primary, immutable, append-only)
- Retention: Years (archival strategy deferred)

**Audit Log**
- Operation, actor, timestamp, resource, before/after state
- Auth events, evidence access, configuration changes
- Storage: Platform DB (primary, immutable, append-only)
- Retention: Years (archival strategy deferred)

### 4.2 Cardinality (PoC Baseline)

- **Policies:** ~10
- **Standards per policy:** ~3
- **Statements per policy:** ~20
- **Checks per statement:** ~2
- **Assets:** ~50
- **Systems per asset:** ~3
- **Total possible (policy, standard, statement, check, asset, system) tuples:** ~360,000
- **Filtered by applicability:** Significantly lower (not every check applies to every system)
- **Check execution frequency:** Configurable via cron-like format strings (e.g., daily, weekly, etc.)
- **Evidence retention:** Years (deferred for PoC)

## 5. Data Flows

### 5.1 Ingestion Flow

```
GRC Tool → OSCAL Ingester → Policy/Standard/Statement Store
Asset Inventory → Asset Sync → Asset Store + Tags
CMDB → CMDB Sync → System Store + Tags
All stores fed into → Orchestrator for check applicability evaluation
```

### 5.2 Check Execution Flow

```
Task Manager (daily schedule) → Orchestrator (evaluate applicability)
→ Build task queue: (policy, standard, statement, check, asset, system)
→ Task Manager assigns to Dispatcher
→ Dispatcher routes to appropriate Runner (inspec, python, agent, api, etc.)
→ Runner executes check, collects output
→ Runner formats evidence into standard model
→ Evidence + signature submitted back to system
→ Evidence Storage (cryptographic validation + append-only logging)
→ Audit Trail updated
```

### 5.3 Query/Reporting Flow

```
Compliance Tool / Risk Management Tool / BI Tool
→ Query API (REST)
→ Evidence Storage
→ Evidence aggregation/grouping (by asset, system, policy, standard, check)
→ Return results
→ Optional: Push evidence to compliance/risk tools
```

## 6. Integration Points

### 6.1 External System Integrations

- **GRC Tool (OSCAL):** Periodic pull (daily/weekly?) to sync policy changes
- **Asset Inventory:** Periodic pull to sync asset changes, tag updates
- **CMDB:** Periodic pull to sync system metadata, tag updates
- **Compliance Tool:** Push evidence on schedule or on-demand; pull query results
- **Risk Management Tool:** Push evidence; pull for gap analysis
- **BI/Reporting Platform:** Query API pull; consume via REST
- **JIRA/ServiceNow:** Query runner integration for human process checks
- **Cloud Services (AWS, Kubernetes, SaaS):** Direct API query runners
- **Log/SIEM:** Query runner integration
- **Config Management (Puppet, Ansible, Terraform):** Query runner integration

### 6.2 Agent/Runner Integrations

- Agents/runners authenticate to system (API key or mTLS certificate)
- Receive task assignments (what to check, where, how)
- Submit evidence back to system
- System validates evidence signature before storage


## 7. Security & Auth (Detailed)

### 7.1 Evidence Integrity

- **Cryptographic Signing:** SHA-256 hash of evidence + asymmetric signature (RSA or EdDSA)
- **Verification:** System maintains public key; verifies signature before storage
- **Tamper Detection:** Signature validation fails if evidence modified

### 7.2 Agent Authentication

- **Service Accounts:** Each agent/runner class gets a service account
- **API Key Auth:** Short-lived JWT tokens (15-min refresh), backed by stored API key hash
- **Certificate Auth:** mTLS with client certificate; certificate must match registered identity
- **Both:** Support both simultaneously for flexibility

### 7.3 Role-Based Access Control (RBAC)

| Role                    | Permissions                                                                                                             |
|--------------------|------------------------------------------------------------------------------------------------------------------------------|
| GRC Engineer       | Manage system config (tag mappings, checks); manage users; run tasks; read all evidence; provide compliance inspection views |
| Policy Engineer    | Provide checks via config repo (does not directly interact with platform)                                                    |
| Auditor            | Read all evidence; cannot modify or run tasks; no config access                                                              |
| Data Consumer / BI Tool | Read evidence via query API; no write access; limited to read-only aggregation queries                                  |

### 7.4 Evidence Access Control

- Optional: Filter evidence by asset/system tags (e.g., show only `business-unit.finance`)

## 8. Technology Stack (PoC)

| Layer                 | Technology (Proposed)                                                               |
|-----------------------|-------------------------------------------------------------------------------------|
| **Language**          | Python 3.14+                                                                        |
| **Framework**         | FastAPI (REST API)                                                                  |
| **Database**          | PostgreSQL                                                                          |
| **Authentication**    | OpenID Connect or custom JWT + mTLS support                                         |
| **Task Scheduling**   | Dramatiq (with additional cron-like format strings in the orchestrator)             |
| **Cryptography**      | cryptography library (Python)                                                       |
| **Check Runners**     | Inspec (CLI), Python SDK (custom), SSH (paramiko), HTTP (requests)                  |
| **Plugin System**     | Python importlib + metadata (pyproject.toml)                                        |
| **Config Management** | YAML (Pydantic for schema validation)                                               |
| **Version Control**   | Git (for plugins, config)                                                           |
| **Containerization**  | Docker (optional, for PoC deployment)                                               |
| **Tests**             | PyTest and factory_boy                                                               |

## 9. Key Design Decisions

1. **Tag-Based Mapping (vs. Explicit Configuration)**
   - Decision: Use hierarchical, tag-based mappings for check applicability
   - Rationale: Scales better than explicit (asset, system) lists; flexible for organization-specific taxonomies

2. **Pluggable Runners (vs. Single Monolithic Check Engine)**
   - Decision: Support multiple execution models (inspec, python, agents, API, etc.)
   - Rationale: Real-world compliance requires checking diverse systems; single approach insufficient

3. **Cryptographic Evidence Signing (vs. Database Constraints Alone)**
   - Decision: Cryptographically sign all evidence; no WORM storage for PoC
   - Rationale: Evidence must be audit-grade; crypto signatures provide portable, verifiable integrity

4. **API-First (vs. UI)**
   - Decision: No UI; provide REST API; let BI tools handle visualization
   - Rationale: Simpler for PoC; flexibility for downstream; BI tools better at reporting

5. **Centralized Orchestrator (vs. Distributed Task Distribution)**
   - Decision: Single orchestrator for PoC; distributed as future enhancement
   - Rationale: Simplifies PoC; defer scaling concerns

6. **Append-Only Evidence Storage (vs. Mutable)**
   - Decision: Evidence immutable; corrections via new records
   - Rationale: Maintains audit trail; prevents accidental/malicious deletion


## 10. Outstanding Questions / TBD

- **Evidence Format Container:** JSON or YAML? (proposed: JSON for API, YAML for human review)
- **Evidence Retention Policy:** Years, but how? Archival strategy? (deferred for PoC)
- **WORM Storage Plugin:** Requirements and integration points? (deferred)
- **Performance Targets:** How fast must evidence be queryable? SLAs? (deferred for PoC)
- **High Availability:** Single-instance acceptable for PoC? Future: distributed orchestrator? (deferred)
- **Intra-System Communication:** gRPC, HTTP, message queue? (proposed: HTTP for simplicity)
- **Plugin Versioning:** How to handle breaking changes in Python SDK? (TBD)
- **Evidence Aggregation:** Pre-compute compliance summaries or query on-demand? (TBD)
- **Retry Strategy Details:** Max retries, backoff curve, which failures retry? (TBD)
- **Multi-Tenancy:** Supported for PoC or future? (Deferred; assume single tenant)


## 11. Future Enhancements (Out of Scope for PoC)

- Distributed orchestrator (multi-region, HA)
- WORM-compliant storage backends
- Advanced evidence retention/archival
- UI dashboard for evidence exploration
- Real-time event-driven check execution (vs. daily batch)
- Machine learning for compliance trend prediction
- Advanced RBAC (attribute-based access control)
- Evidence export/compliance report generation


## Appendix A: Sprint Planning for PoC

This PoC is structured as a 5-sprint delivery, with clear dependencies and end-of-sprint deliverables.

### Sprint 1: Ingestion & Data Foundation

**Goal:** Establish data foundation with external source integrations; design database schema.

**Deliverables:**
- Mock OSCAL ingester (REST endpoint, JSON schema, all-or-nothing validation)
- Mock asset inventory sync (REST endpoint, JSON schema, all-or-nothing validation)
- Mock CMDB sync (REST endpoint, JSON schema, all-or-nothing validation)
- Database schema design (policies, standards, statements, assets, systems, checks, tag mappings, users, roles, evidence, audit logs)
- Gold source ID pattern implementation (dual-path query support)
- Schema mismatch detection and logging (fatal errors logged as evidence)
- Comprehensive unit tests for schema validation and ingestion logic

**Key Dependencies:** None (foundation layer)

**Success Criteria:** External sources mockable; data can be ingested and stored; gold source IDs queryable


### Sprint 2: Orchestration, Config Management & Task Framework

**Goal:** Implement check applicability logic, config sync, and task runner framework.

**Deliverables:**
- Tag mapping DSL (hierarchical tag matching, AND/OR conjunctions; e.g., `linux.ubuntu-22.04`)
- Check library loading from config repo (auto-discovery, metadata parsing)
- Config repo sync endpoint (`POST /config/sync`) with schema validation and reference integrity checking
- Check applicability computation (tag DSL evaluation → check matrix)
- Orchestrator implementation (startup, on config sync, on external data refresh, with configured frequency)
- Task runner framework integration (registration on startup, heartbeat monitoring, round-robin dispatch)
- Task scheduling (cron expressions per check, stored in platform config)
- Task manager (queue, state tracking, retry logic with evidence logging)
- Integration tests for applicability computation; unit tests for tag DSL

**Key Dependencies:** Sprint 1 (needs data in database)

**Success Criteria:** Orchestrator computes applicability correctly; tasks can be queued and dispatched to registered runners; config sync validates and loads checks


### Sprint 3: Evidence Collection, Storage & Evidence-Producing Runners

**Goal:** Implement evidence collection pipeline and core runners; evidence cryptographically secured.

**Deliverables:**
- Evidence schema definition (JSON schema; includes check/system/policy/result/timestamp/metadata/signature)
- Evidence normalization layer (converts runner-specific output to standard schema; schema mismatch = fatal error)
- Cryptographic signing (runner-side implementation; private key management on runner filesystem)
- Public key registration/rotation mechanism (runners report keys on startup/rotation; platform stores for verification)
- Evidence storage in PostgreSQL (append-only, hash chain, signature validation, transaction atomicity)
- Evidence submission API (async endpoint: `POST /evidence/submit`)
- Audit log implementation (evidence submission, config change events)
- Runner implementations:
  - Dummy/test runner (for E2E testing)
  - Python SDK runner (with SDK library for check authors)
  - SSH/remote execution runner (for script-based checks)
- E2E tests: full check→execution→evidence collection→storage flow
- Integration tests for individual runners with mocked external systems
- Unit tests for crypto verification, schema validation, evidence normalization

**Key Dependencies:** Sprint 1-2 (needs orchestrated checks, tasks)

**Success Criteria:** Checks execute, evidence collected cryptographically, end-to-end flow works, E2E tests pass


### Sprint 4: Query API & Authorization

**Goal:** Provide queryable access to evidence with role-based access control.

**Deliverables:**
- Evidence query API (REST endpoints: `/evidence`, `/evidence/by-asset-id/:id`, `/evidence/by-policy/:id`, `/evidence/by-check/:id`, etc.)
- Time-range filtering (`?from=YYYY-MM-DD&to=YYYY-MM-DD`)
- Combination queries (e.g., asset + policy + time range)
- Aggregation endpoints (compliance summary, trend analysis, gap analysis for GRC engineer inspection)
- User/role/permission management API
- Auth/authz middleware (resource:subresource:action permission schema enforcement)
- Role-based access control implementation (GRC Engineer, Auditor, Data Consumer default roles)
- Field-level evidence access control (hide sensitive fields based on permissions)
- Integration with existing secret management tools (Vault, etc.)
- Integration tests for permission enforcement; unit tests for permission evaluation
- API documentation (OpenAPI/Swagger)

**Key Dependencies:** Sprint 1-3 (needs evidence in storage)

**Success Criteria:** Evidence queryable via API; users can authenticate; permissions enforced; aggregation endpoints work


### Sprint 5: Integration, Additional Runners & Testing

**Goal:** Complete runner ecosystem, comprehensive testing, production readiness.

**Deliverables:**
- Additional runner implementations:
  - Inspec runner (CLI invocation, JSON output parsing)
  - Agent based
  - JIRA/ServiceNow runner (human process evidence)
- End-to-end testing (full flow: ingest → configure → schedule → execute → query)
- Integration tests for all runner types with mocked external systems
- Comprehensive unit test coverage for critical logic:
  - Tag DSL evaluation
  - Applicability computation
  - Crypto verification
  - Permission enforcement
- Performance profiling (evidence storage at scale, query response times)
- Operator documentation (deployment, configuration, troubleshooting)
- Deployment guide (Docker, Kubernetes, or standalone)
- Security hardening review (secret handling, auth mechanisms, crypto implementation)

**Key Dependencies:** Sprint 1-4 (full system required)

**Success Criteria:** All runners implemented; comprehensive test coverage; documentation complete; performance acceptable; system ready for evaluation


## Appendix B: Implementation Notes for Phase 2

The following items are flagged for clarification/implementation during Phase 2 (implementation plan, user stories, E2E test design):

### Schema & Integration Points (Require Detailed Specification)

1. **Ingestion Schemas (Sprint 1)**
   - Define concrete JSON/REST schemas for OSCAL, asset inventory, CMDB inputs
   - Specify required fields, validation rules, error codes
   - Document all-or-nothing semantics (transaction rollback on any field mismatch)

2. **Evidence Schema (Sprint 3)**
   - Finalize JSON schema for evidence submission
   - Document runner-specific metadata fields (extensibility points)
   - Specify signature format, public key ID encoding
   - Create examples for each runner type

3. **Tag DSL (Sprint 2)**
   - Define formal grammar for tag matching (hierarchies, AND/OR logic)
   - Provide worked examples: tag hierarchy → applicability rule → check selection
   - Specify precedence/associativity for conjunctions

4. **Evidence Query API (Sprint 4)**
   - Generate OpenAPI/Swagger spec for all endpoints
   - Document request/response formats, error codes, pagination (if applicable)
   - Specify time-range filtering, combination query semantics
   - Define rate limiting (if any)

### Architectural Decisions Requiring Phase 2 Detail

5. **External Data Refresh Strategy**
   - Define polling intervals per entity type (configurable, with defaults)
   - Specify handling of update conflicts (e.g., same asset updated from two sources)
   - Document consistency guarantees (eventual, strong)

6. **Runner Framework Selection**
   - Evaluate existing task runner libraries (Dramatiq, Celery, RQ, APScheduler, etc.)
   - Decide on Python async model (asyncio, gevent, etc.)
   - Define runner-to-platform communication protocol (REST, gRPC, message queue?)

7. **Evidence Signing & Key Management**
   - Define crypto algorithms (RSA 2048+, EdDSA)
   - Specify key generation, storage, rotation procedures
   - Document public key certificate/attestation if needed

8. **Failure Handling Decision Tree**
   - Define response to each failure mode:
     - Check fails to run (timeout, crash, missing dependency)
     - Runner becomes unavailable (heartbeat missed)
     - Evidence storage fails (disk full, DB down)
     - Config sync references non-existent check
     - External data refresh fails
   - Specify retry strategies, alert thresholds, operational runbooks

9. **Database Optimization**
   - Index strategy (gold-source IDs confirmed; others TBD)
   - Partitioning strategy (deferred post-PoC, but design for it)
   - Query performance targets

10. **Secret Rotation & Credential Management**
    - Define rotation intervals for API keys, certificates
    - Specify impact on in-flight operations (runners, API clients)
    - Integration with Vault/Secrets Manager

### Testing Strategy (For User Story Definition)

11. **Unit Test Coverage**
    - Tag DSL evaluation logic
    - Applicability computation
    - Evidence schema validation
    - Crypto verification
    - Permission enforcement
    - **Target:** >80% coverage for critical paths

12. **Integration Testing**
    - Each runner type with mocked external systems
    - Config sync with schema validation
    - End-to-end: ingest → config → execute → query flow
    - Permission enforcement across APIs

13. **End-to-End Testing**
    - Full workflow with dummy runner
    - Snapshot evidence state at key points
    - Query and verify evidence is correct
    - **Automation:** Automated E2E tests as part of CI/CD

### Known Post-PoC Improvements

- Webhooks/notifications for external data changes (instead of polling)
- Applicability versioning (track which rules were active when evidence collected)
- Evidence retention/archival policy (years → specific schedule, WORM export)
- Auth/authz logging (comprehensive audit of all decisions)
- Standard library of approved compensating controls
- Multi-tenancy (instance-per-tenant model defined; schema migration strategy TBD)
- UI dashboard (visualization, compliance reporting, investigation)
- Real-time event-driven check execution (vs. scheduled)
- ML-based compliance trend prediction, anomaly detection
- Approach for dealing with compensating controls (potentially library of controls with applicability based on tags)
