from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlmodel import Field, Relationship, SQLModel

from app.models.base import BaseModel, GoldSourceMixin, PublicModel, TagsMixin

if TYPE_CHECKING:
    from app.models.asset import Asset

asset_system = sa.Table(
    "asset_system",
    BaseModel.metadata,  # pyright: ignore[reportAttributeAccessIssue]  # SQLModel exposes metadata via SQLAlchemy
    sa.Column("asset_id", sa.Integer, sa.ForeignKey("asset.id"), primary_key=True),
    sa.Column("system_id", sa.Integer, sa.ForeignKey("system.id"), primary_key=True),
)


class SystemBase(GoldSourceMixin, TagsMixin, SQLModel):
    primary_fqdn: str = Field(nullable=False)


class System(SystemBase, BaseModel, table=True):
    __tablename__ = "system"  # pyright: ignore[reportAssignmentType]  # SQLAlchemy declared_attr

    assets: list["Asset"] = Relationship(
        sa_relationship_kwargs={"secondary": asset_system, "lazy": "selectin"},
    )


class SystemCreate(SystemBase):
    pass


class SystemPublic(SystemBase, PublicModel):
    asset_ids: list[int] = []
