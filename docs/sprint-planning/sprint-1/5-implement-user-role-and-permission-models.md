### Implement User, Role and Permission Models

**Deps:** T2 — Base Model Mixins and Gold Source ID Pattern

- Create `app/models/user.py` with the following models:
  - `User`: id, username, email, `api_key_hash` (str, nullable), is_active (bool), timestamps via `TimestampMixin`
  - `Role`: id, name, description, timestamps
  - `Permission`: id, resource (str), subresource (str, nullable), action (str), timestamps. Unique constraint on `(resource, subresource, action)`.
  - `UserRole`: link table with `user_id` FK and `role_id` FK
  - `RolePermission`: link table with `role_id` FK and `permission_id` FK
- Define SQLModel `Relationship` fields so that User → Roles → Permissions can be navigated in queries
- Generate an Alembic migration for all auth tables
- Create `tests/factories/user.py` with factories for `User`, `Role`, `Permission`
- Create tests: create a User, assign a Role, attach Permissions to the Role, query the User's permissions through the full relationship chain

**Done:** User can be created and assigned a Role; Role can have Permissions attached; querying a User's permissions traverses User → UserRole → Role → RolePermission → Permission correctly; inserting a duplicate `(resource, subresource, action)` Permission raises `IntegrityError`.
