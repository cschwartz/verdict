from pydantic import BaseModel

from app.models.asset import AssetPublic


class AssetListResponse(BaseModel):
    assets: list[AssetPublic]
    total: int
