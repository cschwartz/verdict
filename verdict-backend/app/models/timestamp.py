from datetime import datetime
from typing import Any, cast

import sqlalchemy as sa
from sqlmodel import Field, SQLModel


class TimestampMixin(SQLModel):
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
