# Mock Services

External APIs are simulated by lightweight FastAPI applications under `mock-services/`. Each mock service loads fixture data from YAML files and serves it through endpoints that mirror the real external API structure (index and detail).

## Factory

Mock services are built using `create_mock_app` from `mock-services/mock_helpers.py`. The factory takes a data directory, a Pydantic model class, and the item's ID field name, then returns a FastAPI app with index and detail endpoints. This avoids duplicating the same boilerplate across mock services — each mock module only needs to define its models and point to its YAML fixture file.

## YAML Fixtures

Fixture data lives in `<mock-service>/data/*.yaml`. Each file contains a list of records that the mock serves. The `load_yaml` helper resolves paths and enforces that they fall within the `mock-services/` base directory to prevent path traversal.

## Usage

Mock services are used both in local development (started via devenv process manager) and in tests. E2E tests start mock services as background processes and configure the backend to point at them. Unit and integration tests use `respx` to mock HTTP calls instead, avoiding the need for running mock services.

Mock services are intentionally simple and untested — their purpose is to provide deterministic, schema-valid responses for development and testing.
