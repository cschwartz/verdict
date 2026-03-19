# Routes and Responses

## Route Handlers

Route handlers are thin. They call into service functions or query methods, receive typed Results, and convert them to HTTP responses using the `unwrap_or_raise` / `unwrap_optional_or_raise` helpers from the error handling pattern.

List endpoints support offset/limit pagination. Lookup endpoints return 404 when no record matches. Ingestion endpoints trigger the pipeline, commit on success, and return the count of ingested records. On failure they return 502 Bad Gateway, since the ingestion endpoint acts as a gateway to external sources and failures originate upstream (fetch errors, invalid responses).

## Response Types

`XPublic` models (defined in `app/models/`) are the default API response type for individual item endpoints. For simple models (no relationships), routes pass `public_class=XPublic` to query functions (`get_by_id`, `get_paginated`, `get_by_gold_source`), which return the narrowed type directly.

For models with ORM relationships that need derived fields (e.g., `asset_ids`), routes query the ORM model and convert via a `_to_public` helper that populates the derived fields from the loaded relationship.

For endpoints that require joined or enriched data beyond the model's own fields (e.g., `GET /users/{id}` returning the user's assigned role names), a schema class under `app/schemas/` extends `XPublic` with the additional fields. These schemas are used as the `response_model` for that specific endpoint; the list endpoint for the same resource continues to use `XPublic` directly to avoid N+1 queries.

List endpoints use lightweight wrapper schemas (e.g., `AssetListResponse`, `UserListResponse`) under `app/schemas/` that pair a list of `XPublic` items with a `total` count.
