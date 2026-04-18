"""add llm_cache table for DB-backed response caching

Revision ID: f3a2b1c9d7e4
Revises: e5f9a3b1c2d8
Create Date: 2026-04-01 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "f3a2b1c9d7e4"
down_revision: Union[str, None] = "e5f9a3b1c2d8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "llm_cache",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("cache_key", sa.String(64), nullable=False, unique=True, index=True),
        sa.Column("agent", sa.String(100), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("llm_cache")
