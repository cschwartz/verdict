from pydantic import BaseModel


class FullIngestionResponse(BaseModel):
    assets_ingested: int
    systems_ingested: int


class UserIngestionResponse(BaseModel):
    users_ingested: int
