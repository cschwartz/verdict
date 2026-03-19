from pydantic import BaseModel, Field

from app.models.user import _ROLE_NAME_PATTERN


class PermissionConfig(BaseModel):
    resource: str
    subresource: str | None = None
    action: str


class RoleConfig(BaseModel):
    name: str = Field(pattern=_ROLE_NAME_PATTERN)
    gold_source_id: str
    permissions: list[PermissionConfig]
