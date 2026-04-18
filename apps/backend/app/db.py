import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/aimarketing"
)

engine = create_engine(DATABASE_URL, future=True)


# Register pgvector type with every psycopg v3 connection so SQLAlchemy can
# serialize Python lists to the PostgreSQL `vector` type and vice versa.
# Without this, inserts of vector data silently fail with psycopg v3.
try:
    from pgvector.psycopg import register_vector

    @event.listens_for(engine, "connect")
    def _register_vector(dbapi_conn, _):
        register_vector(dbapi_conn)

except Exception:
    pass  # pgvector not installed or not using psycopg v3 — vector ops degrade gracefully


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
