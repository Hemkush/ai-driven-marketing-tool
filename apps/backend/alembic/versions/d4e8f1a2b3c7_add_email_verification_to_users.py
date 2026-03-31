"""add email verification fields to users

Revision ID: d4e8f1a2b3c7
Revises: a3f1b2c4d8e9
Create Date: 2026-03-31 00:00:00.000000

"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "d4e8f1a2b3c7"
down_revision: Union[str, None] = "a3f1b2c4d8e9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("users", sa.Column("verification_token", sa.String(128), nullable=True))
    op.add_column("users", sa.Column("token_expires_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_users_verification_token", "users", ["verification_token"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_users_verification_token", table_name="users")
    op.drop_column("users", "token_expires_at")
    op.drop_column("users", "verification_token")
    op.drop_column("users", "is_verified")
