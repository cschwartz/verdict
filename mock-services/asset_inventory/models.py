from pydantic import BaseModel


class AssetIndexItem(BaseModel):
    id: str
    name: str


class AssetItem(BaseModel):
    id: str
    name: str
    description: str
    tags: list[str]
