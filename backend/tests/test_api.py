"""API tests: the whole fairness loop through HTTP, on a throwaway in-memory database."""

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from database import get_session
from main import app


def future_saturday(hour: int) -> str:
    """An Amsterdam time on the coming Saturday, so tests never fall into the past."""
    today = date.today()
    saturday = today + timedelta(days=(5 - today.weekday()) % 7 or 7)
    return datetime.combine(saturday, time(hour), ZoneInfo("Europe/Amsterdam")).isoformat()


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)

    def test_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = test_session
    yield TestClient(app)
    app.dependency_overrides.clear()


def make_club(client):
    club = client.post("/api/clubs", json={"name": "Test FC"}).json()
    return club["id"], {"X-Coordinator-Token": club["coordinator_token"]}


def published_shift(client):
    """One member, available for one weight-3 shift, scheduled and published."""
    club_id, headers = make_club(client)
    member = client.post(
        f"/api/clubs/{club_id}/members", json={"name": "Anna"}, headers=headers
    ).json()
    shift_type = client.post(
        f"/api/clubs/{club_id}/shift-types", json={"name": "Bar", "weight": 3}, headers=headers
    ).json()
    shift = client.post(
        f"/api/clubs/{club_id}/shifts",
        json={
            "shift_type_id": shift_type["id"],
            "starts_at": future_saturday(7),
            "ends_at": future_saturday(10),
            "slots": 1,
        },
        headers=headers,
    ).json()
    token = member["access_token"]
    client.put(f"/api/me/{token}/availability", json={"shift_ids": [shift["id"]]})
    client.post(f"/api/clubs/{club_id}/schedule/publish", headers=headers)
    return club_id, headers, token


def test_coordinator_actions_need_the_right_token(client):
    club_id, headers = make_club(client)
    url = f"/api/clubs/{club_id}/members"
    assert client.post(url, json={"name": "Anna"}).status_code == 422
    assert (
        client.post(
            url, json={"name": "Anna"}, headers={"X-Coordinator-Token": "wrong"}
        ).status_code
        == 403
    )
    assert client.post(url, json={"name": "Anna"}, headers=headers).status_code == 201


def test_coordinator_link_check(client):
    club_id, headers = make_club(client)
    assert client.get(f"/api/clubs/{club_id}/coordinator", headers=headers).status_code == 200
    assert (
        client.get(
            f"/api/clubs/{club_id}/coordinator", headers={"X-Coordinator-Token": "x"}
        ).status_code
        == 403
    )


def test_unknown_member_link_is_404(client):
    assert client.get("/api/me/not-a-real-token").status_code == 404


def test_member_sees_their_assignment(client):
    _, _, token = published_shift(client)
    me = client.get(f"/api/me/{token}").json()
    assert me["name"] == "Anna" and me["balance"] == 0
    assert client.get(f"/api/me/{token}/shifts").json()[0]["assigned"] is True


def test_member_cannot_untick_an_assigned_shift(client):
    _, _, token = published_shift(client)
    response = client.put(f"/api/me/{token}/availability", json={"shift_ids": []})
    assert response.status_code == 409


def test_done_adds_points_and_no_double_counting(client):
    club_id, headers, token = published_shift(client)
    assignment = client.get(f"/api/clubs/{club_id}/assignments").json()[0]
    assert assignment["member_name"] == "Anna" and assignment["shift_type"] == "Bar"

    url = f"/api/assignments/{assignment['id']}"
    assert client.patch(url, json={"status": "done"}, headers=headers).status_code == 200
    assert client.patch(url, json={"status": "done"}, headers=headers).status_code == 409
    assert client.get(f"/api/me/{token}").json()["balance"] == 3


def test_shift_time_without_offset_is_rejected(client):
    club_id, headers = make_club(client)
    shift_type = client.post(
        f"/api/clubs/{club_id}/shift-types", json={"name": "Bar", "weight": 3}, headers=headers
    ).json()
    response = client.post(
        f"/api/clubs/{club_id}/shifts",
        json={
            "shift_type_id": shift_type["id"],
            "starts_at": "2026-10-24T07:00:00",
            "ends_at": "2026-10-24T10:00:00",
            "slots": 1,
        },
        headers=headers,
    )
    assert response.status_code == 422


def test_times_come_back_in_utc(client):
    club_id, headers = make_club(client)
    shift_type = client.post(
        f"/api/clubs/{club_id}/shift-types", json={"name": "Bar", "weight": 3}, headers=headers
    ).json()
    client.post(
        f"/api/clubs/{club_id}/shifts",
        json={
            "shift_type_id": shift_type["id"],
            "starts_at": "2026-10-24T07:00:00+02:00",
            "ends_at": "2026-10-24T10:00:00+02:00",
            "slots": 1,
        },
        headers=headers,
    )
    shift = client.get(f"/api/clubs/{club_id}/shifts").json()[0]
    assert shift["starts_at"] == "2026-10-24T05:00:00Z"


def test_only_the_coordinator_can_list_member_links(client):
    club_id, headers = make_club(client)
    client.post(f"/api/clubs/{club_id}/members", json={"name": "Anna"}, headers=headers)
    url = f"/api/clubs/{club_id}/members/links"

    assert client.get(url).status_code == 422
    assert client.get(url, headers={"X-Coordinator-Token": "wrong"}).status_code == 403
    links = client.get(url, headers=headers).json()
    assert links[0]["name"] == "Anna" and links[0]["access_token"]


def test_public_member_list_never_shows_tokens(client):
    club_id, headers = make_club(client)
    client.post(f"/api/clubs/{club_id}/members", json={"name": "Anna"}, headers=headers)
    assert "access_token" not in client.get(f"/api/clubs/{club_id}/members").json()[0]


def test_weekly_shifts_keep_local_time_across_the_clock_change(client):
    club_id, headers = make_club(client)
    shift_type = client.post(
        f"/api/clubs/{club_id}/shift-types", json={"name": "Bar", "weight": 3}, headers=headers
    ).json()
    response = client.post(
        f"/api/clubs/{club_id}/shifts/weekly",
        json={
            "shift_type_id": shift_type["id"],
            "starts_at": "2026-10-17T07:00:00+02:00",
            "ends_at": "2026-10-17T11:00:00+02:00",
            "slots": 2,
            "weeks": 3,
        },
        headers=headers,
    )
    assert response.status_code == 201
    amsterdam = ZoneInfo("Europe/Amsterdam")
    local_starts = [
        datetime.fromisoformat(s["starts_at"]).astimezone(amsterdam).strftime("%Y-%m-%d %H:%M")
        for s in response.json()
    ]
    assert local_starts == ["2026-10-17 07:00", "2026-10-24 07:00", "2026-10-31 07:00"]


def test_member_with_history_stays(client):
    club_id, headers, _ = published_shift(client)
    anna = client.get(f"/api/clubs/{club_id}/members/links", headers=headers).json()[0]
    assert (
        client.delete(f"/api/clubs/{club_id}/members/{anna['id']}", headers=headers).status_code
        == 409
    )

    bram = client.post(
        f"/api/clubs/{club_id}/members", json={"name": "Bram"}, headers=headers
    ).json()
    assert (
        client.delete(f"/api/clubs/{club_id}/members/{bram['id']}", headers=headers).status_code
        == 204
    )
    assert [m["name"] for m in client.get(f"/api/clubs/{club_id}/members").json()] == ["Anna"]


def test_only_unscheduled_shifts_can_be_deleted(client):
    club_id, headers, _ = published_shift(client)
    scheduled = client.get(f"/api/clubs/{club_id}/shifts").json()[0]
    url = f"/api/clubs/{club_id}/shifts/{scheduled['id']}"
    assert client.delete(url).status_code == 422
    assert client.delete(url, headers=headers).status_code == 409

    shift_type = client.get(f"/api/clubs/{club_id}/shift-types").json()[0]
    extra = client.post(
        f"/api/clubs/{club_id}/shifts",
        json={
            "shift_type_id": shift_type["id"],
            "starts_at": "2026-10-31T07:00:00+01:00",
            "ends_at": "2026-10-31T10:00:00+01:00",
            "slots": 1,
        },
        headers=headers,
    ).json()
    assert (
        client.delete(f"/api/clubs/{club_id}/shifts/{extra['id']}", headers=headers).status_code
        == 204
    )
    assert len(client.get(f"/api/clubs/{club_id}/shifts").json()) == 1


def test_shift_type_in_use_cannot_be_deleted(client):
    club_id, headers, _ = published_shift(client)
    in_use = client.get(f"/api/clubs/{club_id}/shift-types").json()[0]
    assert (
        client.delete(
            f"/api/clubs/{club_id}/shift-types/{in_use['id']}", headers=headers
        ).status_code
        == 409
    )

    unused = client.post(
        f"/api/clubs/{club_id}/shift-types", json={"name": "Driving", "weight": 2}, headers=headers
    ).json()
    assert (
        client.delete(
            f"/api/clubs/{club_id}/shift-types/{unused['id']}", headers=headers
        ).status_code
        == 204
    )


def test_partly_filled_shift_gets_refilled(client):
    club_id, headers = make_club(client)
    anna = client.post(
        f"/api/clubs/{club_id}/members", json={"name": "Anna"}, headers=headers
    ).json()
    bram = client.post(
        f"/api/clubs/{club_id}/members", json={"name": "Bram"}, headers=headers
    ).json()
    shift_type = client.post(
        f"/api/clubs/{club_id}/shift-types", json={"name": "Bar", "weight": 3}, headers=headers
    ).json()
    shift = client.post(
        f"/api/clubs/{club_id}/shifts",
        json={
            "shift_type_id": shift_type["id"],
            "starts_at": future_saturday(7),
            "ends_at": future_saturday(10),
            "slots": 2,
        },
        headers=headers,
    ).json()

    client.put(f"/api/me/{anna['access_token']}/availability", json={"shift_ids": [shift["id"]]})
    first = client.post(f"/api/clubs/{club_id}/schedule/publish", headers=headers).json()
    assert [a["member_name"] for a in first["assignments"]] == ["Anna"]
    assert first["unfilled"] == [{"shift_id": shift["id"], "missing": 1}]

    client.put(f"/api/me/{bram['access_token']}/availability", json={"shift_ids": [shift["id"]]})
    second = client.post(f"/api/clubs/{club_id}/schedule/generate", headers=headers).json()
    assert [a["member_name"] for a in second["assignments"]] == ["Bram"]
    assert second["unfilled"] == []


def test_past_shifts_are_hidden_and_never_scheduled(client):
    club_id, headers = make_club(client)
    member = client.post(
        f"/api/clubs/{club_id}/members", json={"name": "Anna"}, headers=headers
    ).json()
    shift_type = client.post(
        f"/api/clubs/{club_id}/shift-types", json={"name": "Bar", "weight": 3}, headers=headers
    ).json()
    shifts_url = f"/api/clubs/{club_id}/shifts"
    past = client.post(
        shifts_url,
        json={
            "shift_type_id": shift_type["id"],
            "starts_at": "2020-01-04T07:00:00+01:00",
            "ends_at": "2020-01-04T10:00:00+01:00",
            "slots": 1,
        },
        headers=headers,
    ).json()
    upcoming = client.post(
        shifts_url,
        json={
            "shift_type_id": shift_type["id"],
            "starts_at": future_saturday(7),
            "ends_at": future_saturday(10),
            "slots": 1,
        },
        headers=headers,
    ).json()

    token = member["access_token"]
    assert [s["id"] for s in client.get(f"/api/me/{token}/shifts").json()] == [upcoming["id"]]
    assert (
        client.put(f"/api/me/{token}/availability", json={"shift_ids": [past["id"]]}).status_code
        == 422
    )

    proposal = client.post(f"/api/clubs/{club_id}/schedule/generate", headers=headers).json()
    assert past["id"] not in [u["shift_id"] for u in proposal["unfilled"]]
