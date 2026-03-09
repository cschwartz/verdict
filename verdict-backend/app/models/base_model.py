from datetime import datetime
from typing import Any, cast

import sqlalchemy as sa
from sqlmodel import Field, SQLModel


class BaseModel(SQLModel):
    """Base for all table models. Provides an auto-increment primary key and timestamps."""

    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime | None = Field(
        default=None,
        sa_type=cast("type[Any]", sa.DateTime(timezone=True)),
        sa_column_kwargs={"server_default": sa.func.now(), "nullable": False},
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_type=cast("type[Any]", sa.DateTime(timezone=True)),
        sa_column_kwargs={
            "server_default": sa.func.now(),
            "onupdate": sa.func.clock_timestamp(),
            "nullable": False,
        },
    )


class PublicModel(SQLModel):
    """Mixin for public/read models. Provides narrowed id and timestamps."""

    id: int
    created_at: datetime
    updated_at: datetime
