"""create system and asset_system tables

Revision ID: 3bfa8f122226
Revises: 6b960c32fa67
Create Date: 2026-03-03 22:34:22.098102

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3bfa8f122226"
down_revision: str | Sequence[str] | None = "6b960c32fa67"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "system",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tags", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("gold_source_id", sa.String(), nullable=False),
        sa.Column("gold_source_type", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("primary_fqdn", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("gold_source_type", "gold_source_id"),
    )
    op.create_table(
        "asset_system",
        sa.Column("asset_id", sa.Integer(), nullable=False),
        sa.Column("system_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["asset.id"]),
        sa.ForeignKeyConstraint(["system_id"], ["system.id"]),
        sa.PrimaryKeyConstraint("asset_id", "system_id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("asset_system")
    op.drop_table("system")
