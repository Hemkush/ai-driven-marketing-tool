"""add payload_json to positioning_statements

Revision ID: e3a7c9b2d1f4
Revises: f2b9a8c1d4e7
Create Date: 2026-03-24 12:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e3a7c9b2d1f4"
down_revision: Union[str, Sequence[str], None] = "f2b9a8c1d4e7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "positioning_statements" not in inspector.get_table_names():
        return

    columns = {c["name"] for c in inspector.get_columns("positioning_statements")}
    if "payload_json" not in columns:
        op.add_column(
            "positioning_statements",
            sa.Column("payload_json", sa.Text(), nullable=False, server_default="{}"),
        )

    # Backfill existing rows using known columns.
    bind.execute(
        sa.text(
            """
            UPDATE positioning_statements
            SET payload_json = jsonb_build_object(
                'positioning_statement', statement_text,
                'rationale', rationale,
                'target_segment', '',
                'key_differentiators', '[]'::jsonb,
                'proof_points', '[]'::jsonb
            )::text
            WHERE payload_json IS NULL
               OR payload_json = ''
               OR payload_json = '{}'
            """
        )
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "positioning_statements" not in inspector.get_table_names():
        return
    columns = {c["name"] for c in inspector.get_columns("positioning_statements")}
    if "payload_json" in columns:
        op.drop_column("positioning_statements", "payload_json")
