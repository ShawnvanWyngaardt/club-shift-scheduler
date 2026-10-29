"""Create a permanent demo club and print its links.

Run locally:        uv run python seed.py
Run against Neon:   set DATABASE_URL in a terminal opened for that job only, then the same command
On a fresh database, run `uv run alembic upgrade head` first.
"""
from sqlmodel import Session

from database import engine
from sandbox import create_demo_club

if __name__ == "__main__":
    with Session(engine) as session:
        club, members = create_demo_club(session, is_demo=False)

        print(f"Club '{club.name}' created with id {club.id}")
        print(f"Coordinator token: {club.coordinator_token}\n")
        print("Member links:")
        for member in members:
            print(f"  {member.name:<8} /api/me/{member.access_token}/shifts")
