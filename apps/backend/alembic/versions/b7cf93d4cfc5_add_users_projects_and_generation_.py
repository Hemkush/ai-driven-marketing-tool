"""add users projects and generation project link

Revision ID: b7cf93d4cfc5
Revises: c5ce00361ea6
Create Date: 2026-03-03 22:20:45.722688

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7cf93d4cfc5'
down_revision: Union[str, Sequence[str], None] = 'c5ce00361ea6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "generations" not in tables:
        return

    columns = {c["name"] for c in inspector.get_columns("generations")}
    if "project_id" not in columns:
        op.add_column("generations", sa.Column("project_id", sa.Integer(), nullable=True))

    indexes = {i["name"] for i in inspector.get_indexes("generations")}
    if "ix_generations_project_id" not in indexes:
        op.create_index(
            "ix_generations_project_id",
            "generations",
            ["project_id"],
            unique=False,
        )

    fk_names = {
        fk.get("name")
        for fk in inspector.get_foreign_keys("generations")
        if fk.get("name")
    }
    if (
        "projects" in tables
        and "fk_generations_project_id_projects" not in fk_names
    ):
        op.create_foreign_key(
            "fk_generations_project_id_projects",
            "generations",
            "projects",
            ["project_id"],
            ["id"],
        )


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "generations" not in tables:
        return

    fk_names = {
        fk.get("name")
        for fk in inspector.get_foreign_keys("generations")
        if fk.get("name")
    }
    if "fk_generations_project_id_projects" in fk_names:
        op.drop_constraint(
            "fk_generations_project_id_projects",
            "generations",
            type_="foreignkey",
        )

    indexes = {i["name"] for i in inspector.get_indexes("generations")}
    if "ix_generations_project_id" in indexes:
        op.drop_index("ix_generations_project_id", table_name="generations")

    columns = {c["name"] for c in inspector.get_columns("generations")}
    if "project_id" in columns:
        op.drop_column("generations", "project_id")
