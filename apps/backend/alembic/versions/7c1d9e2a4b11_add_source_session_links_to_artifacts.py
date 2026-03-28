"""add source_session_id links to generated artifact tables

Revision ID: 7c1d9e2a4b11
Revises: e3a7c9b2d1f4
Create Date: 2026-03-25 15:20:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7c1d9e2a4b11"
down_revision: Union[str, Sequence[str], None] = "e3a7c9b2d1f4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


ARTIFACT_TABLES = [
    "analysis_reports",
    "positioning_statements",
    "research_reports",
    "persona_profiles",
    "channel_strategies",
    "roadmap_plans",
    "media_assets",
]


def _fk_name(table_name: str) -> str:
    short = {
        "analysis_reports": "analysis_reports",
        "positioning_statements": "positioning_stmt",
        "research_reports": "research_reports",
        "persona_profiles": "persona_profiles",
        "channel_strategies": "channel_strat",
        "roadmap_plans": "roadmap_plans",
        "media_assets": "media_assets",
    }
    return f"fk_{short.get(table_name, table_name)}_src_session"


def _add_source_session_column(table_name: str) -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if table_name not in inspector.get_table_names():
        return

    columns = {c["name"] for c in inspector.get_columns(table_name)}
    if "source_session_id" in columns:
        return

    op.add_column(table_name, sa.Column("source_session_id", sa.Integer(), nullable=True))
    op.create_index(
        op.f(f"ix_{table_name}_source_session_id"),
        table_name,
        ["source_session_id"],
        unique=False,
    )
    op.create_foreign_key(
        _fk_name(table_name),
        table_name,
        "questionnaire_sessions",
        ["source_session_id"],
        ["id"],
    )


def _backfill_source_session_column(table_name: str) -> None:
    bind = op.get_bind()
    bind.execute(
        sa.text(
            f"""
            UPDATE {table_name} AS artifact
            SET source_session_id = (
                SELECT qs.id
                FROM questionnaire_sessions AS qs
                WHERE qs.project_id = artifact.project_id
                  AND qs.created_at <= artifact.created_at
                ORDER BY qs.created_at DESC, qs.id DESC
                LIMIT 1
            )
            WHERE artifact.source_session_id IS NULL
            """
        )
    )


def upgrade() -> None:
    for table_name in ARTIFACT_TABLES:
        _add_source_session_column(table_name)
    for table_name in ARTIFACT_TABLES:
        _backfill_source_session_column(table_name)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    for table_name in reversed(ARTIFACT_TABLES):
        if table_name not in inspector.get_table_names():
            continue
        columns = {c["name"] for c in inspector.get_columns(table_name)}
        if "source_session_id" not in columns:
            continue
        op.drop_constraint(
            _fk_name(table_name),
            table_name,
            type_="foreignkey",
        )
        op.drop_index(op.f(f"ix_{table_name}_source_session_id"), table_name=table_name)
        op.drop_column(table_name, "source_session_id")
