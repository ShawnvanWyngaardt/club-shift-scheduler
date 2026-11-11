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
    assignment = first_assignment(client, club_id, headers)
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


def test_club_data_needs_the_coordinator_link(client):
    club_id, headers, _ = published_shift(client)
    wrong = {"X-Coordinator-Token": "wrong"}
    for path in ("members", "assignments", "ledger"):
        url = f"/api/clubs/{club_id}/{path}"
        assert client.get(url, headers=wrong).status_code == 403
        assert client.get(url, headers=headers).status_code == 200


def test_members_see_all_balances_but_only_their_own_history(client):
    club_id, headers, token = published_shift(client)
    sam = add_member(client, club_id, headers, "Sam")
    assignment = first_assignment(client, club_id, headers)
    client.patch(f"/api/assignments/{assignment['id']}", json={"status": "done"}, headers=headers)

    mine = client.get(f"/api/me/{token}/ledger").json()
    assert "Sam" in {b["name"] for b in mine["balances"]}
    assert mine["entries"]
    assert all(e["member_id"] == assignment["member_id"] for e in mine["entries"])

    assert client.get(f"/api/me/{sam['access_token']}/ledger").json()["entries"] == []
    assert client.get("/api/me/nonsense/ledger").status_code == 404


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
    assert [
        m["name"] for m in client.get(f"/api/clubs/{club_id}/members", headers=headers).json()
    ] == ["Anna"]


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
    assert first["unfilled"] == [
        {
            "shift_id": shift["id"],
            "missing": 1,
            "blocked": [
                {"member_id": anna["id"], "member_name": "Anna", "reason": "already_on_shift"}
            ],
        }
    ]

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


def test_member_sees_their_assignments_and_outcomes(client):
    club_id, headers, token = published_shift(client)

    mine = client.get(f"/api/me/{token}/assignments").json()
    assert [(a["shift_type"], a["status"]) for a in mine] == [("Bar", "assigned")]

    client.patch(f"/api/assignments/{mine[0]['id']}", json={"status": "done"}, headers=headers)
    assert client.get(f"/api/me/{token}/assignments").json()[0]["status"] == "done"

    me = client.get(f"/api/me/{token}").json()
    links = client.get(f"/api/clubs/{club_id}/members/links", headers=headers).json()
    assert me["member_id"] == links[0]["id"]
    assert me["balance"] == 3


def first_assignment(client, club_id, headers):
    return client.get(f"/api/clubs/{club_id}/assignments", headers=headers).json()[0]


def add_member(client, club_id, headers, name):
    return client.post(f"/api/clubs/{club_id}/members", json={"name": name}, headers=headers).json()


def test_coordinator_can_take_someone_off_a_shift(client):
    club_id, headers, token = published_shift(client)
    assignment = first_assignment(client, club_id, headers)
    url = f"/api/assignments/{assignment['id']}"

    assert client.delete(url, headers={"X-Coordinator-Token": "wrong"}).status_code == 403
    assert client.delete(url, headers=headers).status_code == 204

    assert client.get(f"/api/me/{token}/assignments").json() == []
    shifts = client.get(f"/api/me/{token}/shifts").json()
    assert not any(s["available"] for s in shifts if s["id"] == assignment["shift_id"])

    # A refill doesn't hand the shift straight back to the same member.
    client.post(f"/api/clubs/{club_id}/schedule/publish", headers=headers)
    refilled = client.get(f"/api/clubs/{club_id}/assignments", headers=headers).json()
    assert all(a["member_id"] != assignment["member_id"] for a in refilled)


def test_coordinator_can_give_a_shift_to_someone_else(client):
    club_id, headers, token = published_shift(client)
    assignment = first_assignment(client, club_id, headers)
    sam = add_member(client, club_id, headers, "Sam")

    candidates = client.get(
        f"/api/assignments/{assignment['id']}/candidates", headers=headers
    ).json()
    ids = [c["member_id"] for c in candidates]
    assert sam["id"] in ids
    assert assignment["member_id"] not in ids

    moved = client.put(
        f"/api/assignments/{assignment['id']}/member",
        json={"member_id": sam["id"]},
        headers=headers,
    )
    assert moved.status_code == 200
    assert first_assignment(client, club_id, headers)["member_name"] == "Sam"
    assert client.get(f"/api/me/{token}/assignments").json() == []


def test_busy_members_and_recorded_outcomes_are_protected(client):
    club_id, headers, _ = published_shift(client)
    assignment = first_assignment(client, club_id, headers)
    url = f"/api/assignments/{assignment['id']}"

    # Sam takes another shift at exactly the same time.
    sam = add_member(client, club_id, headers, "Sam")
    type_id = client.get(f"/api/clubs/{club_id}/shift-types").json()[0]["id"]
    same_time = client.post(
        f"/api/clubs/{club_id}/shifts",
        json={
            "shift_type_id": type_id,
            "starts_at": assignment["starts_at"],
            "ends_at": assignment["ends_at"],
            "slots": 1,
        },
        headers=headers,
    ).json()
    client.put(f"/api/me/{sam['access_token']}/availability", json={"shift_ids": [same_time["id"]]})
    client.post(f"/api/clubs/{club_id}/schedule/publish", headers=headers)

    candidates = client.get(f"{url}/candidates", headers=headers).json()
    assert next(c for c in candidates if c["member_id"] == sam["id"])["busy"]
    moved = client.put(f"{url}/member", json={"member_id": sam["id"]}, headers=headers)
    assert moved.status_code == 409

    # Once an outcome is recorded, the assignment is history.
    client.patch(url, json={"status": "done"}, headers=headers)
    assert client.delete(url, headers=headers).status_code == 409


def same_time_shift(client, club_id, headers, assignment, slots):
    type_id = client.get(f"/api/clubs/{club_id}/shift-types").json()[0]["id"]
    return client.post(
        f"/api/clubs/{club_id}/shifts",
        json={
            "shift_type_id": type_id,
            "starts_at": assignment["starts_at"],
            "ends_at": assignment["ends_at"],
            "slots": slots,
        },
        headers=headers,
    ).json()


def test_preview_explains_empty_slots(client):
    club_id, headers, token = published_shift(client)
    assignment = first_assignment(client, club_id, headers)
    shift = same_time_shift(client, club_id, headers, assignment, slots=1)

    # Only the member who is already busy at that time says yes.
    client.put(
        f"/api/me/{token}/availability",
        json={"shift_ids": [assignment["shift_id"], shift["id"]]},
    )
    preview = client.post(f"/api/clubs/{club_id}/schedule/generate", headers=headers).json()
    gap = next(u for u in preview["unfilled"] if u["shift_id"] == shift["id"])
    assert gap["blocked"] == [
        {
            "member_id": assignment["member_id"],
            "member_name": assignment["member_name"],
            "reason": "busy_at_that_time",
        }
    ]


def test_coordinator_can_fill_an_open_slot_by_hand(client):
    club_id, headers, _ = published_shift(client)
    assignment = first_assignment(client, club_id, headers)
    shift = same_time_shift(client, club_id, headers, assignment, slots=2)
    url = f"/api/clubs/{club_id}/shifts/{shift['id']}"
    sam = add_member(client, club_id, headers, "Sam")
    tom = add_member(client, club_id, headers, "Tom")

    busy = {
        c["member_id"]: c["busy"] for c in client.get(f"{url}/candidates", headers=headers).json()
    }
    assert busy[assignment["member_id"]] and not busy[sam["id"]]

    wrong = {"X-Coordinator-Token": "wrong"}
    assert (
        client.post(f"{url}/assignments", json={"member_id": sam["id"]}, headers=wrong).status_code
        == 403
    )
    assert (
        client.post(
            f"{url}/assignments", json={"member_id": sam["id"]}, headers=headers
        ).status_code
        == 201
    )
    busy_member = {"member_id": assignment["member_id"]}
    assert client.post(f"{url}/assignments", json=busy_member, headers=headers).status_code == 409
    assert (
        client.post(
            f"{url}/assignments", json={"member_id": tom["id"]}, headers=headers
        ).status_code
        == 201
    )

    uma = add_member(client, club_id, headers, "Uma")
    full = client.post(f"{url}/assignments", json={"member_id": uma["id"]}, headers=headers)
    assert full.status_code == 409
