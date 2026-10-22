"""Database connection and session handling."""
import os
from collections.abc import Iterator
from pathlib import Path

from dotenv import load_dotenv
from sqlmodel import Session, SQLModel, create_engine

# `neon deploy` writes the Neon connection strings to .env.local in the repo root.
# Variables already set in the environment (e.g. by the host) take precedence.
load_dotenv(Path(__file__).resolve().parent.parent / ".env.local")

# DATABASE_URL is Neon's pooled connection; without it we fall back to a local SQLite file.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./local.db")

# Neon gives "postgresql://"; SQLAlchemy needs to be told which driver to use.
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgresql://", "postgresql+psycopg://", 1)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith(
    "sqlite") else {}
engine = create_engine(
    DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)


def create_tables() -> None:
    """Create any tables that don't exist yet."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    """Give each request its own database session, closed afterwards."""
    with Session(engine) as session:
        yield session
