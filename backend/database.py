"""Database connection and session handling."""
import os
from collections.abc import Iterator

from sqlmodel import Session, SQLModel, create_engine

# Local default is a SQLite file; production sets DATABASE_URL (Planned for Thursday).
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./local.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith(
    "sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)


def create_tables() -> None:
    """Create any tables that don't exist yet."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    """Give each request its own database session, closed afterwards."""
    with Session(engine) as session:
        yield session
