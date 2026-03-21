"""add memory chunks with pgvector

Revision ID: f2b9a8c1d4e7
Revises: a1f2b3c4d5e6
Create Date: 2026-03-20 10:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f2b9a8c1d4e7"
down_revision: Union[str, Sequence[str], None] = "a1f2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # pgvector extension (PostgreSQL)
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    if "memory_chunks" not in inspector.get_table_names():
        op.execute(
            """
            CREATE TABLE memory_chunks (
                id SERIAL PRIMARY KEY,
                project_id INTEGER NOT NULL REFERENCES projects(id),
                session_id INTEGER NULL REFERENCES questionnaire_sessions(id),
                response_id INTEGER NULL REFERENCES questionnaire_responses(id),
                source_type VARCHAR(40) NOT NULL DEFAULT 'questionnaire_response',
                topic_tag VARCHAR(80) NULL,
                content_text TEXT NOT NULL,
                content_hash VARCHAR(64) NOT NULL,
                embedding vector(1536) NULL,
                metadata_json TEXT NOT NULL DEFAULT '{}',
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            );
            """
        )

    op.execute("CREATE INDEX IF NOT EXISTS ix_memory_chunks_project_id ON memory_chunks(project_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_memory_chunks_session_id ON memory_chunks(session_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_memory_chunks_response_id ON memory_chunks(response_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_memory_chunks_content_hash ON memory_chunks(content_hash);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_memory_chunks_id ON memory_chunks(id);")
    # Approximate nearest neighbor for cosine distance
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_memory_chunks_embedding_ivfflat
        ON memory_chunks USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100);
        """
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "memory_chunks" in inspector.get_table_names():
        op.execute("DROP TABLE memory_chunks;")
