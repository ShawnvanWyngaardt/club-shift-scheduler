"""Database connection and session handling."""
import os
from collections.abc import Iterator

from sqlmodel import Session, create_engine

# Local development uses a SQLite file. Production (Render) sets DATABASE_URL to Neon.
# To work against Neon locally, set DATABASE_URL in a terminal opened for that job only.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./local.db")

# Neon gives "postgresql://"; SQLAlchemy needs to be told which driver to use.
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgresql://", "postgresql+psycopg://", 1)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith(
    "sqlite") else {}
engine = create_engine(
    DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)


def get_session() -> Iterator[Session]:
    """Give each request its own database session, closed afterwards."""
    with Session(engine) as session:
        yield session
