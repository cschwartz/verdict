from pydantic import BaseModel


class AssetIndexItem(BaseModel):
    """Shape of a single asset in the external inventory's list response."""

    id: str
    name: str


class AssetDetail(BaseModel):
    """Shape of a single asset in the external inventory's detail response."""

    id: str
    name: str
    description: str
    tags: list[str]
