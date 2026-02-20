# Verdict

Verdict is a proof-of-concept for a compliance automation and evidence collection platform that bridges governance, business architecture, and technical infrastructure. It automatically discovers which compliance checks apply to which systems via tag-based mappings, executes those checks through pluggable backends, and collects cryptographically signed evidence in a tamper-proof store.

This PoC is being developed with strongly guided AI support — architecture, design, and implementation are human-directed, with AI tooling used throughout the development process.

## Architecture

Verdict connects three layers of abstraction:

- **Governance Layer** — OSCAL policies, standards, and statements ingested from a GRC tool
- **Business Architecture** — IT-asset inventory with ITIL-level abstractions (protection requirements, threat classifications)
- **Technical Layer** — CMDB with concrete systems, hostnames, IPs, and technical metadata

The platform ingests data from these sources, computes check applicability using a hierarchical tag DSL, orchestrates check execution across pluggable runners (Python SDK, InSpec, SSH, agents), and stores append-only, cryptographically signed evidence queryable via REST API.

Key design decisions: API-first (no UI), tag-based check applicability, pluggable execution backends, and cryptographic evidence signing.

For the full architecture, see [`docs/architecture-design-document.md`](docs/architecture-design-document.md).

## Tech Stack

| Component        | Technology                  |
|------------------|-----------------------------|
| Language         | Python 3.14+                |
| Framework        | FastAPI                     |
| Database         | PostgreSQL                  |
| Migrations       | Alembic                     |
| Task Scheduling  | Dramatiq                    |
| Tests            | pytest + factory_boy        |
| Package Manager  | uv                          |

## Prerequisites

- [devenv](https://devenv.sh/) (provides Nix-managed development environment including PostgreSQL, Python, and git hooks)

## Setup

1. **Enter the devenv shell** (from the repo root or `verdict-backend/`):

   ```sh
   devenv shell
   ```

   This provisions PostgreSQL, Python, uv, and configures git pre-commit hooks (ruff, ruff-format, mypy).

2. **Run the setup recipe** (from `verdict-backend/`):

   ```sh
   cd verdict-backend
   just setup
   ```

   This will:
   - Install Python dependencies via `uv sync`
   - Wait for PostgreSQL to be ready
   - Run database migrations via Alembic

## Development

All commands run from `verdict-backend/`:

```sh
just dev              # Start FastAPI dev server (localhost:8000)
just test             # Run tests
just test-cov         # Run tests with coverage
just check            # Format + lint + type-check
just db-migrate       # Apply migrations
just db-reset         # Drop and recreate the dev database
just db-shell         # Open pgcli
```

Run `just` with no arguments to see all available recipes.
