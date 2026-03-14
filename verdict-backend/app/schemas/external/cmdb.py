from pydantic import BaseModel


class SystemIndexItem(BaseModel):
    id: str
    primary_fqdn: str


class SystemDetail(BaseModel):
    id: str
    primary_fqdn: str
    asset_gold_source_ids: list[str]
    tags: list[str]
