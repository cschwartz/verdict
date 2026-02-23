from datetime import datetime

import sqlalchemy as sa
from sqlmodel import Field


class TimestampMixin:
    created_at: datetime = Field(
        sa_column=sa.Column(
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        )
    )
    updated_at: datetime = Field(
        sa_column=sa.Column(
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.clock_timestamp(),
            nullable=False,
        )
    )
