from pydantic import BaseModel

from app.schemas.base import GoldSourceResponseMixin, TagsResponseMixin, TimestampResponseMixin


class AssetResponse(TimestampResponseMixin, GoldSourceResponseMixin, TagsResponseMixin):
    id: int
    name: str
    description: str


class AssetListResponse(BaseModel):
    assets: list[AssetResponse]
    total: int


class IngestionResponse(BaseModel):
    ingested: int
