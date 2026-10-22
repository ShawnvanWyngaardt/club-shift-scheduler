"""Create a demo club with members, shifts, availability and some earlier points.

Run locally:            uv run python seed.py
Run against Neon:       set DATABASE_URL first, then the same command
"""
import random
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlmodel import Session

from database import create_tables, engine
from models import Availability, Club, Member, PointsEntry, Shift, ShiftType

MEMBER_NAMES = ["Anouk", "Bram", "Daan", "Emma",
                "Fleur", "Jesse", "Lotte", "Milan", "Noa", "Sem"]

# (name, weight, how likely members are to volunteer for it)
SHIFT_TYPES = [
    ("Bar, early Saturday", 3, 0.25),
    ("Youth referee", 2, 0.45),
    ("Field setup", 1, 0.6),
]

# (shift type name, start hour, end hour, slots), repeated each Saturday
SATURDAY = [
    ("Field setup", 8, 9, 2),
    ("Bar, early Saturday", 7, 11, 2),
    ("Youth referee", 9, 11, 3),
]

CLUB_TZ = ZoneInfo("Europe/Amsterdam")  # shift times are stored timezone-aware

# Points members already earned this season, so the fairness rule has something to work with
EARLIER_POINTS = {"Anouk": 6, "Bram": 4, "Emma": 3, "Milan": 1}


def next_saturday() -> date:
    today = date.today()
    days_ahead = (5 - today.weekday()) % 7 or 7  # Monday is 0, Saturday is 5
    return today + timedelta(days=days_ahead)


def seed(weeks: int = 2) -> None:
    rng = random.Random(42)  # same "random" data every run
    create_tables()

    with Session(engine) as session:
        club = Club(name="VV Demo")
        session.add(club)
        session.flush()  # gives the club its id without saving yet

        members = [Member(name=name, club_id=club.id) for name in MEMBER_NAMES]
        types = {
            name: ShiftType(name=name, weight=weight, club_id=club.id)
            for name, weight, _ in SHIFT_TYPES
        }
        session.add_all(members + list(types.values()))
        session.flush()

        likelihood = {name: chance for name, _, chance in SHIFT_TYPES}
        first = next_saturday()
        for week in range(weeks):
            day = first + timedelta(weeks=week)
            for type_name, start, end, slots in SATURDAY:
                shift = Shift(
                    club_id=club.id,
                    shift_type_id=types[type_name].id,
                    starts_at=datetime.combine(day, time(start), CLUB_TZ),
                    ends_at=datetime.combine(day, time(end), CLUB_TZ),
                    slots=slots,
                )
                session.add(shift)
                session.flush()
                for member in members:
                    if rng.random() < likelihood[type_name]:
                        session.add(Availability(
                            member_id=member.id, shift_id=shift.id))

        for member in members:
            if member.name in EARLIER_POINTS:
                session.add(
                    PointsEntry(
                        member_id=member.id,
                        change=EARLIER_POINTS[member.name],
                        reason="done: earlier shifts this season",
                    )
                )

        session.commit()

        print(f"Club '{club.name}' created with id {club.id}")
        print(f"Coordinator token: {club.coordinator_token}\n")
        print("Member links:")
        for member in members:
            print(f"  {member.name:<8} /api/me/{member.access_token}/shifts")


if __name__ == "__main__":
    seed()
