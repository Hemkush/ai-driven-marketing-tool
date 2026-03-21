"""add business address to projects

Revision ID: a1f2b3c4d5e6
Revises: 9a6b2d4e7f01
Create Date: 2026-03-11 12:10:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1f2b3c4d5e6"
down_revision: Union[str, Sequence[str], None] = "9a6b2d4e7f01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "projects" not in inspector.get_table_names():
        return
    columns = {c["name"] for c in inspector.get_columns("projects")}
    if "business_address" not in columns:
        op.add_column("projects", sa.Column("business_address", sa.String(length=500), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "projects" not in inspector.get_table_names():
        return
    columns = {c["name"] for c in inspector.get_columns("projects")}
    if "business_address" in columns:
        op.drop_column("projects", "business_address")
