### Set Up GitHub Actions CI for verdict-backend

**Deps:** None

The repo is a monorepo with `verdict-backend/` as one project directory. Locally, devenv provisions PostgreSQL 16, Python (via uv), just, and git-hooks. CI should use devenv itself to avoid duplicating environment setup and risking drift.

- Create `.github/workflows/verdict-backend.yaml` with a workflow that:
  - Triggers on push and pull request when files under `verdict-backend/`, devenv config files (`devenv.nix`, `devenv.yaml`, `devenv.lock`, `shared/`), or the workflow file itself change (use `paths` filter)
  - Runs on `ubuntu-latest`
  - Checks out the repo with `actions/checkout@v5`
  - Installs Nix via `cachix/install-nix-action@v31`
  - Sets up the devenv cache via `cachix/cachix-action@v16` with `name: devenv`
  - Installs devenv via `nix profile install nixpkgs#devenv`
  - Starts devenv services in the background (`devenv up -d` in `verdict-backend/`) to bring up PostgreSQL with the same config as local dev (databases `verdict` and `verdict_test` auto-created by `initialDatabases`)
  - Waits for PostgreSQL to be ready (e.g. `pg_isready` loop or similar)
  - Runs the following using `devenv shell bash -- -e {0}` as the shell (with `working-directory: verdict-backend`):
    1. `just db-migrate` — apply Alembic migrations
    2. `just check` — ruff format, ruff lint, mypy
    3. `just test` — pytest
- Investigate whether `devenv test` can replace the manual `devenv up -d` + command steps (it builds the shell and runs git hooks, but may not start services or run custom test commands — verify and document the decision)

**Done:** Pushing a change under `verdict-backend/` or devenv config triggers the workflow; devenv provisions the full environment including PostgreSQL; `just check` and `just test` run using the same toolchain as local development; changes outside the relevant paths do not trigger the workflow.
