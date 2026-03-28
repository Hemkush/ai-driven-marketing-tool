"""add conversation_analysis_json to questionnaire_sessions

Revision ID: a3f1b2c4d8e9
Revises: 7c1d9e2a4b11
Create Date: 2026-03-27 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "a3f1b2c4d8e9"
down_revision: Union[str, None] = "7c1d9e2a4b11"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "questionnaire_sessions",
        sa.Column("conversation_analysis_json", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("questionnaire_sessions", "conversation_analysis_json")
