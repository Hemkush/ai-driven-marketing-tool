"""pending_registrations table + remove verification cols from users

Revision ID: e5f9a3b1c2d8
Revises: d4e8f1a2b3c7
Create Date: 2026-03-31 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "e5f9a3b1c2d8"
down_revision: Union[str, None] = "d4e8f1a2b3c7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create pending_registrations table
    op.create_table(
        "pending_registrations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("token", sa.String(128), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_pending_registrations_email", "pending_registrations", ["email"], unique=True)
    op.create_index("ix_pending_registrations_token", "pending_registrations", ["token"], unique=True)

    # Remove verification columns from users (added in d4e8f1a2b3c7)
    op.drop_index("ix_users_verification_token", table_name="users")
    op.drop_column("users", "token_expires_at")
    op.drop_column("users", "verification_token")

    # Mark all existing users as already verified (set is_verified=true then drop col)
    op.execute("UPDATE users SET is_verified = true")
    op.drop_column("users", "is_verified")


def downgrade() -> None:
    op.add_column("users", sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="true"))
    op.add_column("users", sa.Column("verification_token", sa.String(128), nullable=True))
    op.add_column("users", sa.Column("token_expires_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_users_verification_token", "users", ["verification_token"], unique=False)
    op.drop_index("ix_pending_registrations_token", table_name="pending_registrations")
    op.drop_index("ix_pending_registrations_email", table_name="pending_registrations")
    op.drop_table("pending_registrations")
