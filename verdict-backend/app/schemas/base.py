from datetime import datetime

from pydantic import BaseModel


class TimestampResponseMixin(BaseModel):
    created_at: datetime
    updated_at: datetime


class GoldSourceResponseMixin(BaseModel):
    gold_source_id: str
    gold_source_type: str


class TagsResponseMixin(BaseModel):
    tags: list[str]
