"""The demo club: built for the seed script, and for every visitor who clicks "Try the demo".

Demo clubs are flagged and removed after a day, so visitors never see each other's changes.
"""
import random
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import delete
from sqlmodel import Session, col, func, select

from models import Assignment, Availability, Club, Member, PointsEntry, Shift, ShiftType

CLUB_TZ = ZoneInfo("Europe/Amsterdam")

VISITOR_NAME = "You"
MEMBER_NAMES = ["Anouk", "Bram", "Daan", "Emma", "Fleur", "Jesse", "Lotte", "Milan", "Noa", "Sem"]

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

# Points members already earned this season, so the fairness rule has something to work with
EARLIER_POINTS = {"Anouk": 6, "Bram": 4, "Emma": 3, "Milan": 1}

DEMO_LIFETIME = timedelta(hours=24)
MAX_DEMO_CLUBS = 200


def next_saturday() -> date:
    today = date.today()
    days_ahead = (5 - today.weekday()) % 7 or 7  # Monday is 0, Saturday is 5
    return today + timedelta(days=days_ahead)


def create_demo_club(
    session: Session, *, is_demo: bool = True, weeks: int = 2
) -> tuple[Club, list[Member]]:
    """Build and save a club with members, shifts, availability and some earlier points.
    Demo clubs also get a member called "You", with no answers yet, for the visitor to play."""
    rng = random.Random(42)  # same "random" data every time

    club = Club(name="VV Demo", is_demo=is_demo)
    session.add(club)
    session.flush()  # gives the club its id without saving yet

    names = ([VISITOR_NAME] if is_demo else []) + MEMBER_NAMES
    members = [Member(name=name, club_id=club.id) for name in names]
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
                # The visitor starts with nothing ticked: their choices are theirs to make.
                if member.name != VISITOR_NAME and rng.random() < likelihood[type_name]:
                    session.add(Availability(member_id=member.id, shift_id=shift.id))

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
    return club, members


def delete_club(session: Session, club_id: int) -> None:
    """Remove a club and everything that belongs to it, children before parents."""
    member_ids = select(Member.id).where(Member.club_id == club_id)
    session.execute(delete(Availability).where(col(Availability.member_id).in_(member_ids)))
    session.execute(delete(Assignment).where(col(Assignment.member_id).in_(member_ids)))
    session.execute(delete(PointsEntry).where(col(PointsEntry.member_id).in_(member_ids)))
    session.execute(delete(Shift).where(col(Shift.club_id) == club_id))
    session.execute(delete(ShiftType).where(col(ShiftType.club_id) == club_id))
    session.execute(delete(Member).where(col(Member.club_id) == club_id))
    session.execute(delete(Club).where(col(Club.id) == club_id))


def remove_expired_demos(session: Session) -> int:
    """Delete demo clubs older than a day. Clubs from the seed script are never touched."""
    cutoff = datetime.now(timezone.utc) - DEMO_LIFETIME
    expired = list(
        session.exec(
            select(Club.id).where(col(Club.is_demo).is_(True), col(Club.created_at) < cutoff)
        )
    )
    for club_id in expired:
        delete_club(session, club_id)
    session.commit()
    return len(expired)


def demo_capacity_reached(session: Session) -> bool:
    """A ceiling on live demo clubs, so nobody can fill the database by clicking repeatedly."""
    count = session.exec(
        select(func.count()).select_from(Club).where(col(Club.is_demo).is_(True))
    ).one()
    return count >= MAX_DEMO_CLUBS
