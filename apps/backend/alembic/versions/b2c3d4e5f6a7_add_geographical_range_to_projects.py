"""add geographical range to projects

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-04-18 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "projects" not in inspector.get_table_names():
        return
    columns = {c["name"] for c in inspector.get_columns("projects")}
    if "geographical_range" not in columns:
        op.add_column("projects", sa.Column("geographical_range", sa.String(length=500), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "projects" not in inspector.get_table_names():
        return
    columns = {c["name"] for c in inspector.get_columns("projects")}
    if "geographical_range" in columns:
        op.drop_column("projects", "geographical_range")
