# Routes and Responses

## Route Handlers

Route handlers are thin. They call into service functions or query methods, receive typed Results, and convert them to HTTP responses using the `unwrap_or_raise` / `unwrap_optional_or_raise` helpers from the error handling pattern.

List endpoints support offset/limit pagination. Lookup endpoints return 404 when no record matches. Ingestion endpoints trigger the pipeline, commit on success, and return the count of ingested records. On failure they return 502 Bad Gateway, since the ingestion endpoint acts as a gateway to external sources and failures originate upstream (fetch errors, invalid responses).

## Response Types

`XPublic` models (defined in `app/models/`) serve directly as API response types. There is no separate response schema layer — `XPublic` is used as the `response_model` in route decorators and as the return type of route handlers.

For simple models (no relationships), routes pass `public_class=XPublic` to query functions (`get_by_id`, `get_paginated`, `get_by_gold_source`), which return the narrowed type directly.

For models with relationships that need derived fields (e.g., `asset_ids`), routes query the ORM model and convert via a `_to_public` helper that populates the derived fields from the loaded relationship.

List endpoints use lightweight wrapper schemas (e.g., `AssetListResponse`) under `app/schemas/` that pair a list of `XPublic` items with a `total` count. These are the only response schemas — individual item responses use `XPublic` directly.
