import sqlalchemy as sa
from sqlmodel import Field, Relationship, SQLModel

from app.models.base_model import BaseModel, PublicModel
from app.models.gold_source import GoldSourceMixin

# --- Link tables (defined first; referenced by link_model= below) ---


class UserRole(SQLModel, table=True):
    __tablename__ = "userrole"  # pyright: ignore[reportAssignmentType]

    user_id: int | None = Field(default=None, foreign_key="app_user.id", primary_key=True)
    role_id: int | None = Field(default=None, foreign_key="role.id", primary_key=True)


class RolePermission(SQLModel, table=True):
    __tablename__ = "rolepermission"  # pyright: ignore[reportAssignmentType]

    role_id: int | None = Field(default=None, foreign_key="role.id", primary_key=True)
    permission_id: int | None = Field(default=None, foreign_key="permission.id", primary_key=True)


# --- Permission ---


class PermissionBase(SQLModel):
    resource: str = Field(nullable=False)
    subresource: str | None = Field(default=None)
    action: str = Field(nullable=False)


class Permission(PermissionBase, BaseModel, table=True):
    __tablename__ = "permission"  # pyright: ignore[reportAssignmentType]
    __table_args__ = (sa.UniqueConstraint("resource", "subresource", "action"),)


class PermissionPublic(PermissionBase, PublicModel):
    pass


# --- Role ---


_ROLE_NAME_PATTERN = r"^[a-z][a-z0-9-]*$"


class RoleBase(GoldSourceMixin, SQLModel):
    name: str = Field(
        nullable=False, regex=_ROLE_NAME_PATTERN
    )  # SQLModel uses pydantic v1-style `regex`
    description: str = Field(default="", nullable=False)


class Role(RoleBase, BaseModel, table=True):
    __tablename__ = "role"  # pyright: ignore[reportAssignmentType]
    __table_args__ = (*GoldSourceMixin.__table_args__, sa.UniqueConstraint("name"))  # type: ignore[assignment]  # extending base tuple with additional constraint

    permissions: list["Permission"] = Relationship(link_model=RolePermission)


class RolePublic(RoleBase, PublicModel):
    pass


class RoleCreate(RoleBase):
    pass


# --- User ---


class UserBase(GoldSourceMixin, SQLModel):
    username: str = Field(nullable=False)
    email: str = Field(nullable=False)
    is_active: bool = Field(default=True)


class User(UserBase, BaseModel, table=True):
    __tablename__ = "app_user"  # pyright: ignore[reportAssignmentType]

    roles: list["Role"] = Relationship(link_model=UserRole)


class UserPublic(UserBase, PublicModel):
    pass


class UserCreate(UserBase):
    pass
