from typing import Any, cast

from sqlalchemy_json import MutableJson
from sqlmodel import Field, SQLModel


class TagsMixin(SQLModel):
    tags: list[str] = Field(
        default_factory=list,
        sa_type=cast("type[Any]", MutableJson),
        sa_column_kwargs={"nullable": False, "server_default": "[]"},
    )
