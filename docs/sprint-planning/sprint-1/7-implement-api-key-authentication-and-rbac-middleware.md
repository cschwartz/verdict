### Implement API Key Authentication and RBAC Middleware

**Deps:** T5 — User, Role and Permission Models

- Create `app/auth/dependencies.py` with a `get_current_user` FastAPI dependency that:
  - Reads the `X-API-Key` header from the request
  - Hashes the provided key and looks up a User by matching `api_key_hash`
  - Returns the User with loaded permissions (via role relationships)
  - Raises HTTP 401 if the key is missing, invalid, or the user is inactive
- Create `app/auth/permissions.py` with a `require_permission(resource, subresource, action)` dependency factory that:
  - Depends on `get_current_user`
  - Checks that the resolved User has the required permission via their Roles
  - Raises HTTP 403 if the permission is not found
- Store API keys as hashes — never persist plaintext keys. Use a one-way hash (e.g. SHA-256 or similar) so that keys can be verified but not recovered.
- Create `app/auth/__init__.py`
- Create integration tests: request with valid API key resolves the correct User; request with invalid or missing key returns 401; request with valid key but insufficient permissions returns 403; request with valid key and correct permission succeeds

**Done:** Valid API key resolves to correct User with loaded permissions; invalid/missing key returns 401; request with valid key but insufficient permissions returns 403; `require_permission()` dependency is composable on any endpoint. mTLS/certificate auth deferred to Sprint 2.
