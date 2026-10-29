"""Demo sandboxes: one per visitor, cleaned up after a day, and capped in number."""
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

import sandbox
from database import get_session
from main import app
from models import Club, Member


@pytest.fixture
def engine():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def client(engine):
    def test_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = test_session
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_demo_gives_a_working_sandbox(client):
    response = client.post("/api/demo")
    assert response.status_code == 201
    demo = response.json()

    headers = {"X-Coordinator-Token": demo["coordinator_token"]}
    assert client.get(
        f"/api/clubs/{demo['club_id']}/coordinator", headers=headers).status_code == 200

    visitor = demo["members"][0]
    assert visitor["name"] == "You" and visitor["points"] == 0
    shifts = client.get(f"/api/me/{visitor['token']}/shifts").json()
    assert len(shifts) == 6
    assert not any(shift["available"] for shift in shifts)


def test_every_visitor_gets_their_own_club(client):
    first = client.post("/api/demo").json()
    second = client.post("/api/demo").json()
    assert first["club_id"] != second["club_id"]


def test_expired_demos_are_removed(client, engine):
    old = client.post("/api/demo").json()
    with Session(engine) as session:
        club = session.get(Club, old["club_id"])
        club.created_at = datetime.now(timezone.utc) - timedelta(hours=25)
        session.add(club)
        session.commit()

    client.post("/api/demo")  # every new demo clears out expired ones first

    # Ids can be reused after a delete (SQLite does), so look the old club up by its token.
    old_member_token = old["members"][0]["token"]
    with Session(engine) as session:
        club = session.exec(
            select(Club).where(Club.coordinator_token ==
                               old["coordinator_token"])
        ).first()
        member = session.exec(select(Member).where(
            Member.access_token == old_member_token)).first()
        assert club is None
        assert member is None


def test_seeded_clubs_are_never_removed(engine):
    with Session(engine) as session:
        club, _ = sandbox.create_demo_club(session, is_demo=False)
        club.created_at = datetime.now(timezone.utc) - timedelta(days=30)
        session.add(club)
        session.commit()
        club_id = club.id

        sandbox.remove_expired_demos(session)

    with Session(engine) as session:
        assert session.get(Club, club_id) is not None


def test_demo_limit_protects_the_database(client, monkeypatch):
    monkeypatch.setattr(sandbox, "MAX_DEMO_CLUBS", 1)
    assert client.post("/api/demo").status_code == 201
    assert client.post("/api/demo").status_code == 503
