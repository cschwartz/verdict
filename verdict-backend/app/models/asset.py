from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

from app.models.base import BaseModel, GoldSourceMixin, PublicModel, TagsMixin

if TYPE_CHECKING:
    from app.models.system import System


class AssetBase(GoldSourceMixin, TagsMixin, SQLModel):
    name: str = Field(nullable=False)
    description: str = Field(default="", nullable=False)


class Asset(AssetBase, BaseModel, table=True):
    __tablename__ = "asset"  # pyright: ignore[reportAssignmentType]  # SQLAlchemy declared_attr

    systems: list["System"] = Relationship(
        sa_relationship_kwargs={
            "secondary": "asset_system",
            "lazy": "selectin",
            "viewonly": True,
        },
    )


class AssetCreate(AssetBase):
    pass


class AssetPublic(AssetBase, PublicModel):
    pass
