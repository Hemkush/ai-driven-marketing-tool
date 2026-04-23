"""add trust layer: quality_score, consent_given, output_feedback

Revision ID: c1d2e3f4a5b6
Revises: a1b2c3d4e5f6
Create Date: 2026-04-22 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "c1d2e3f4a5b6"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("analysis_reports",       sa.Column("quality_score", sa.Float(), nullable=True))
    op.add_column("positioning_statements", sa.Column("quality_score", sa.Float(), nullable=True))
    op.add_column("persona_profiles",       sa.Column("quality_score", sa.Float(), nullable=True))
    op.add_column("research_reports",       sa.Column("quality_score", sa.Float(), nullable=True))
    op.add_column("roadmap_plans",          sa.Column("quality_score", sa.Float(), nullable=True))
    op.add_column("media_assets",           sa.Column("quality_score", sa.Float(), nullable=True))
    op.add_column("projects",               sa.Column("consent_given", sa.Boolean(), nullable=True, server_default="true"))

    op.create_table(
        "output_feedback",
        sa.Column("id",            sa.Integer(),  primary_key=True, index=True),
        sa.Column("project_id",    sa.Integer(),  sa.ForeignKey("projects.id"), nullable=True, index=True),
        sa.Column("agent",         sa.String(50), nullable=False),
        sa.Column("quality_score", sa.Float(),    nullable=True),
        sa.Column("polarity",      sa.SmallInteger(), nullable=False),
        sa.Column("created_at",    sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("output_feedback")
    op.drop_column("projects", "consent_given")
    op.drop_column("media_assets", "quality_score")
    op.drop_column("roadmap_plans", "quality_score")
    op.drop_column("research_reports", "quality_score")
    op.drop_column("persona_profiles", "quality_score")
    op.drop_column("positioning_statements", "quality_score")
    op.drop_column("analysis_reports", "quality_score")
