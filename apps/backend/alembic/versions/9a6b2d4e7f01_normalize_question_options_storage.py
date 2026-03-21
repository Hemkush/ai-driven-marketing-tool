"""normalize question options storage

Revision ID: 9a6b2d4e7f01
Revises: 54c3c445c9d4
Create Date: 2026-03-11 11:15:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9a6b2d4e7f01"
down_revision: Union[str, Sequence[str], None] = "54c3c445c9d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "questionnaire_responses" not in inspector.get_table_names():
        return

    columns = {c["name"] for c in inspector.get_columns("questionnaire_responses")}

    if "question_options_json" not in columns:
        op.add_column(
            "questionnaire_responses",
            sa.Column(
                "question_options_json",
                sa.Text(),
                nullable=False,
                server_default="[]",
            ),
        )

    # Migrate legacy encoded MCQ options from question_text to question_options_json.
    bind.execute(
        sa.text(
            """
            UPDATE questionnaire_responses
            SET
              question_options_json = (
                to_jsonb(
                  string_to_array(
                    trim(split_part(question_text, '##mcq_options##', 2)),
                    '||'
                  )
                )::text
              ),
              question_text = trim(split_part(question_text, '##mcq_options##', 1))
            WHERE position('##mcq_options##' in question_text) > 0
            """
        )
    )

    bind.execute(
        sa.text(
            """
            UPDATE questionnaire_responses
            SET question_options_json = '[]'
            WHERE question_options_json IS NULL OR question_options_json = ''
            """
        )
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "questionnaire_responses" not in inspector.get_table_names():
        return
    columns = {c["name"] for c in inspector.get_columns("questionnaire_responses")}
    if "question_options_json" in columns:
        op.drop_column("questionnaire_responses", "question_options_json")
