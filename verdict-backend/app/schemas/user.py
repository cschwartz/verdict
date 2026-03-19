from pydantic import BaseModel

from app.models.user import UserPublic


class UserListResponse(BaseModel):
    users: list[UserPublic]
    total: int


class UserDetail(UserPublic):
    roles: list[str]
