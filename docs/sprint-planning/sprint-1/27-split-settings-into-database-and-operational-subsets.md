### Split Settings into Database and Operational Subsets

**Deps:** T3 — Asset Model, Mock Source & Ingestion

The `Settings` class in `app/config.py` requires all configuration fields at import time, including `asset_inventory_url`. This means database-only operations like Alembic migrations fail if operational settings are missing from the environment.

- Extract a `DatabaseSettings` base class with only the fields needed for database connectivity: `database_url`, `database_host`, `database_port`, `database_name`, `database_user`
- Keep the full `Settings` class extending `DatabaseSettings` with all remaining fields (`asset_inventory_url`, `debug`, etc.) still required
- Update Alembic's `env.py` to use `DatabaseSettings` instead of `Settings`
- The application entrypoint continues to use `Settings`, which fails fast at startup if any operational field is missing
- Verify that `just db-migrate` succeeds with only database-related environment variables set
- Verify that `just dev` still fails fast if `ASSET_INVENTORY_URL` is missing

**Done:** Alembic migrations run with only database environment variables; the application still requires the full operational configuration at startup; no change to runtime behaviour.
