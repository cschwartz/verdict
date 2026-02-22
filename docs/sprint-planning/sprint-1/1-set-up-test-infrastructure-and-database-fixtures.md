### Set Up Test Infrastructure and Database Fixtures

**Deps:** None

The test database `verdict_test` is already provisioned by devenv. The app uses SQLModel sessions via `app.db.get_session` (generator-based, synchronous). Settings are in `app.config.Settings` with `DATABASE_NAME_TEST` available in `.env`.

- Create `tests/conftest.py` with a `db_session` fixture that:
  - Builds a test engine pointing at `verdict_test` (construct URL from existing `Settings` fields, substituting `DATABASE_NAME_TEST` for `DATABASE_NAME`)
  - Wraps each test in a transaction and rolls back after the test completes (begin-on-setup, rollback-on-teardown)
  - Yields a `sqlmodel.Session` bound to that transaction
- Create an `app_client` fixture in `tests/conftest.py` that:
  - Overrides the `get_session` dependency on the FastAPI `app` with the `db_session` fixture
  - Returns an `httpx.AsyncClient` configured against the app (using `pytest-asyncio`)
- Create `tests/factories/__init__.py` (empty package for future factory_boy factories)
- Create `tests/test_smoke.py` with two tests:
  - A test that uses `app_client` to `GET /` and asserts a 200 response
  - A test that uses `db_session` to execute `SELECT 1` and asserts the result

**Done:** `db_session` fixture provides a working session connected to `verdict_test` that rolls back after each test; `app_client` fixture can hit endpoints with the DB dependency overridden; smoke tests verify both.
