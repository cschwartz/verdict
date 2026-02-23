import sqlalchemy as sa
from sqlalchemy_json import MutableJson
from sqlmodel import Field


class TagsMixin:
    tags: list[str] = Field(sa_column=sa.Column(MutableJson, nullable=False, server_default="[]"))
