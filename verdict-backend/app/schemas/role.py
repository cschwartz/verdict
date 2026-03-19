from pydantic import BaseModel

from app.models.user import PermissionPublic, RolePublic


class RoleListResponse(BaseModel):
    roles: list[RolePublic]
    total: int


class RoleDetail(RolePublic):
    permissions: list[PermissionPublic]
