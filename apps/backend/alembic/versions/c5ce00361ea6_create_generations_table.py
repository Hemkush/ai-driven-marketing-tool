"""create generations table

Revision ID: c5ce00361ea6
Revises: 
Create Date: 2026-03-03 10:15:44.654383

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c5ce00361ea6'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "users" not in tables:
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("email", sa.String(length=255), nullable=False),
            sa.Column("password_hash", sa.String(length=255), nullable=False),
            sa.Column("full_name", sa.String(length=255), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
        )
        op.create_index("ix_users_id", "users", ["id"], unique=False)
        op.create_index("ix_users_email", "users", ["email"], unique=True)
        tables.add("users")

    if "projects" not in tables:
        op.create_table(
            "projects",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("name", sa.String(length=200), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("owner_id", sa.Integer(), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["owner_id"], ["users.id"]),
        )
        op.create_index("ix_projects_id", "projects", ["id"], unique=False)
        op.create_index("ix_projects_owner_id", "projects", ["owner_id"], unique=False)
        tables.add("projects")

    if "generations" not in tables:
        op.create_table(
            "generations",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column(
                "timestamp",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column("input_json", sa.Text(), nullable=False),
            sa.Column("output_json", sa.Text(), nullable=False),
        )
        op.create_index("ix_generations_id", "generations", ["id"], unique=False)

    # Ensure required MVP tables exist for fresh databases.
    tables = set(sa.inspect(bind).get_table_names())

    if "questionnaire_sessions" not in tables:
        op.create_table(
            "questionnaire_sessions",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("project_id", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(length=40), nullable=False, server_default="in_progress"),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        )
        op.create_index("ix_questionnaire_sessions_id", "questionnaire_sessions", ["id"], unique=False)
        op.create_index(
            "ix_questionnaire_sessions_project_id",
            "questionnaire_sessions",
            ["project_id"],
            unique=False,
        )

    if "questionnaire_responses" not in tables:
        op.create_table(
            "questionnaire_responses",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("session_id", sa.Integer(), nullable=False),
            sa.Column("sequence_no", sa.Integer(), nullable=False),
            sa.Column("question_text", sa.Text(), nullable=False),
            sa.Column("answer_text", sa.Text(), nullable=False, server_default=""),
            sa.Column("question_type", sa.String(length=40), nullable=False, server_default="open_ended"),
            sa.Column("question_options_json", sa.Text(), nullable=False, server_default="[]"),
            sa.Column("source", sa.String(length=40), nullable=False, server_default="system"),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["session_id"], ["questionnaire_sessions.id"]),
        )
        op.create_index(
            "ix_questionnaire_responses_id", "questionnaire_responses", ["id"], unique=False
        )
        op.create_index(
            "ix_questionnaire_responses_session_id",
            "questionnaire_responses",
            ["session_id"],
            unique=False,
        )

    if "analysis_reports" not in tables:
        op.create_table(
            "analysis_reports",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("project_id", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(length=40), nullable=False, server_default="queued"),
            sa.Column("report_json", sa.Text(), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        )
        op.create_index("ix_analysis_reports_id", "analysis_reports", ["id"], unique=False)
        op.create_index(
            "ix_analysis_reports_project_id", "analysis_reports", ["project_id"], unique=False
        )

    if "positioning_statements" not in tables:
        op.create_table(
            "positioning_statements",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("project_id", sa.Integer(), nullable=False),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("statement_text", sa.Text(), nullable=False),
            sa.Column("rationale", sa.Text(), nullable=False, server_default=""),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        )
        op.create_index(
            "ix_positioning_statements_id", "positioning_statements", ["id"], unique=False
        )
        op.create_index(
            "ix_positioning_statements_project_id",
            "positioning_statements",
            ["project_id"],
            unique=False,
        )

    if "research_reports" not in tables:
        op.create_table(
            "research_reports",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("project_id", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(length=40), nullable=False, server_default="queued"),
            sa.Column("report_json", sa.Text(), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        )
        op.create_index("ix_research_reports_id", "research_reports", ["id"], unique=False)
        op.create_index(
            "ix_research_reports_project_id", "research_reports", ["project_id"], unique=False
        )

    if "persona_profiles" not in tables:
        op.create_table(
            "persona_profiles",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("project_id", sa.Integer(), nullable=False),
            sa.Column("persona_name", sa.String(length=160), nullable=False),
            sa.Column("persona_json", sa.Text(), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        )
        op.create_index("ix_persona_profiles_id", "persona_profiles", ["id"], unique=False)
        op.create_index(
            "ix_persona_profiles_project_id", "persona_profiles", ["project_id"], unique=False
        )

    if "channel_strategies" not in tables:
        op.create_table(
            "channel_strategies",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("project_id", sa.Integer(), nullable=False),
            sa.Column("strategy_json", sa.Text(), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        )
        op.create_index("ix_channel_strategies_id", "channel_strategies", ["id"], unique=False)
        op.create_index(
            "ix_channel_strategies_project_id", "channel_strategies", ["project_id"], unique=False
        )

    if "roadmap_plans" not in tables:
        op.create_table(
            "roadmap_plans",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("project_id", sa.Integer(), nullable=False),
            sa.Column("plan_json", sa.Text(), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        )
        op.create_index("ix_roadmap_plans_id", "roadmap_plans", ["id"], unique=False)
        op.create_index(
            "ix_roadmap_plans_project_id", "roadmap_plans", ["project_id"], unique=False
        )

    if "media_assets" not in tables:
        op.create_table(
            "media_assets",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("project_id", sa.Integer(), nullable=False),
            sa.Column("asset_type", sa.String(length=80), nullable=False),
            sa.Column("storage_uri", sa.Text(), nullable=False),
            sa.Column("prompt_text", sa.Text(), nullable=False, server_default=""),
            sa.Column("metadata_json", sa.Text(), nullable=False, server_default="{}"),
            sa.Column("status", sa.String(length=40), nullable=False, server_default="created"),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        )
        op.create_index("ix_media_assets_id", "media_assets", ["id"], unique=False)
        op.create_index("ix_media_assets_project_id", "media_assets", ["project_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    drop_order = [
        "media_assets",
        "roadmap_plans",
        "channel_strategies",
        "persona_profiles",
        "research_reports",
        "positioning_statements",
        "analysis_reports",
        "questionnaire_responses",
        "questionnaire_sessions",
        "generations",
        "projects",
        "users",
    ]
    for table in drop_order:
        if table in tables:
            op.drop_table(table)
