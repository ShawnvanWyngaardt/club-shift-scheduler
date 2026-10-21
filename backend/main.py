"""API entry point for the Club Shift Scheduler."""
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from sqlmodel import Session, col, func, select

from database import create_tables, get_session
from models import (
    Assignment,
    AssignmentPublic,
    Availability,
    AvailabilityUpdate,
    Club,
    ClubCreate,
    ClubPublic,
    ClubWithToken,
    Health,
    Member,
    MemberCreate,
    MemberPublic,
    MemberWithToken,
    MyShift,
    PointsEntry,
    Proposal,
    ProposedAssignment,
    Shift,
    ShiftCreate,
    ShiftPublic,
    ShiftType,
    ShiftTypeCreate,
    ShiftTypePublic,
    UnfilledShift,
)

from solver import MemberIn, Problem, Result, ShiftIn, solve_greedy


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Runs once at startup: make sure the tables exist."""
    create_tables()
    yield


app = FastAPI(title="Club Shift Scheduler", lifespan=lifespan)

SessionDep = Annotated[Session, Depends(get_session)]


def get_club_or_404(session: Session, club_id: int) -> Club:
    """Fetch a club, or stop the request with a 404."""
    club = session.get(Club, club_id)
    if club is None:
        raise HTTPException(status_code=404, detail="Club not found")
    return club


@app.get("/api/health")
def health() -> Health:
    """Lets us (and the host) check the server is running."""
    return Health(status="ok")


@app.post("/api/clubs", response_model=ClubWithToken, status_code=201)
def create_club(data: ClubCreate, session: SessionDep) -> Club:
    club = Club.model_validate(data)
    session.add(club)
    session.commit()
    session.refresh(club)
    return club


@app.get("/api/clubs/{club_id}", response_model=ClubPublic)
def read_club(club_id: int, session: SessionDep) -> Club:
    return get_club_or_404(session, club_id)


@app.post("/api/clubs/{club_id}/members", response_model=MemberWithToken, status_code=201)
def add_member(club_id: int, data: MemberCreate, session: SessionDep) -> Member:
    get_club_or_404(session, club_id)
    member = Member.model_validate(data, update={"club_id": club_id})
    session.add(member)
    session.commit()
    session.refresh(member)
    return member


@app.get("/api/clubs/{club_id}/members", response_model=list[MemberPublic])
def list_members(club_id: int, session: SessionDep) -> list[Member]:
    get_club_or_404(session, club_id)
    return list(session.exec(select(Member).where(Member.club_id == club_id)))


@app.post("/api/clubs/{club_id}/shift-types", response_model=ShiftTypePublic, status_code=201)
def add_shift_type(club_id: int, data: ShiftTypeCreate, session: SessionDep) -> ShiftType:
    get_club_or_404(session, club_id)
    shift_type = ShiftType.model_validate(data, update={"club_id": club_id})
    session.add(shift_type)
    session.commit()
    session.refresh(shift_type)
    return shift_type


@app.get("/api/clubs/{club_id}/shift-types", response_model=list[ShiftTypePublic])
def list_shift_types(club_id: int, session: SessionDep) -> list[ShiftType]:
    get_club_or_404(session, club_id)
    return list(session.exec(select(ShiftType).where(ShiftType.club_id == club_id)))


@app.post("/api/clubs/{club_id}/shifts", response_model=ShiftPublic, status_code=201)
def add_shift(club_id: int, data: ShiftCreate, session: SessionDep) -> Shift:
    get_club_or_404(session, club_id)
    shift_type = session.get(ShiftType, data.shift_type_id)
    if shift_type is None or shift_type.club_id != club_id:
        raise HTTPException(
            status_code=404, detail="Shift type not found in this club")
    shift = Shift.model_validate(data, update={"club_id": club_id})
    session.add(shift)
    session.commit()
    session.refresh(shift)
    return shift


@app.get("/api/clubs/{club_id}/shifts", response_model=list[ShiftPublic])
def list_shifts(club_id: int, session: SessionDep) -> list[Shift]:
    get_club_or_404(session, club_id)
    statement = select(Shift).where(
        Shift.club_id == club_id).order_by(Shift.starts_at)
    return list(session.exec(statement))


def get_member_by_token(token: str, session: Session) -> Member:
    """Find the member behind a personal link, or stop with a 404."""
    member = session.exec(select(Member).where(
        Member.access_token == token)).first()
    if member is None:
        raise HTTPException(status_code=404, detail="Unknown link")
    return member


def my_shifts(member: Member, session: Session) -> list[MyShift]:
    """All shifts in the member's club, each marked with their availability."""
    rows = session.exec(
        select(Shift, ShiftType)
        .where(Shift.club_id == member.club_id, Shift.shift_type_id == ShiftType.id)
        .order_by(Shift.starts_at)
    ).all()
    chosen = set(
        session.exec(select(Availability.shift_id).where(
            Availability.member_id == member.id)).all()
    )
    return [
        MyShift(
            id=shift.id,
            shift_type=shift_type.name,
            starts_at=shift.starts_at,
            ends_at=shift.ends_at,
            available=shift.id in chosen,
        )
        for shift, shift_type in rows
    ]


@app.get("/api/me/{token}/shifts", response_model=list[MyShift])
def read_my_shifts(token: str, session: SessionDep) -> list[MyShift]:
    member = get_member_by_token(token, session)
    return my_shifts(member, session)


@app.put("/api/me/{token}/availability", response_model=list[MyShift])
def update_my_availability(
    token: str, data: AvailabilityUpdate, session: SessionDep
) -> list[MyShift]:
    member = get_member_by_token(token, session)

    club_shift_ids = set(session.exec(
        select(Shift.id).where(Shift.club_id == member.club_id)).all())
    unknown = set(data.shift_ids) - club_shift_ids
    if unknown:
        raise HTTPException(
            status_code=422, detail=f"Not shifts in your club: {sorted(unknown)}")

    # Replace the member's answers completely: remove the old ones, then add the new ones.
    for old in session.exec(select(Availability).where(Availability.member_id == member.id)).all():
        session.delete(old)
    session.flush()
    for shift_id in set(data.shift_ids):
        session.add(Availability(member_id=member.id, shift_id=shift_id))
    session.commit()

    return my_shifts(member, session)

# ---------- Schedule ----------


def points_by_member(club_id: int, session: Session) -> dict[int, int]:
    """Each member's balance: the sum of their ledger entries."""
    rows = session.exec(
        select(PointsEntry.member_id, func.sum(PointsEntry.change))
        .join(Member, PointsEntry.member_id == Member.id)
        .where(Member.club_id == club_id)
        .group_by(PointsEntry.member_id)
    ).all()
    return {member_id: total for member_id, total in rows}


def build_problem(club_id: int, session: Session) -> Problem:
    """Translate database rows into the solver's plain input.
    Only shifts without any assignments yet are scheduled."""
    members = session.exec(select(Member).where(
        Member.club_id == club_id)).all()
    points = points_by_member(club_id, session)

    already_assigned = select(Assignment.shift_id)
    open_shifts = session.exec(
        select(Shift, ShiftType).where(
            Shift.club_id == club_id,
            Shift.shift_type_id == ShiftType.id,
            col(Shift.id).not_in(already_assigned),
        )
    ).all()

    shift_ids = [shift.id for shift, _ in open_shifts]
    available_rows = session.exec(
        select(Availability.member_id, Availability.shift_id).where(
            col(Availability.shift_id).in_(shift_ids)
        )
    ).all()

    return Problem(
        members=[MemberIn(id=m.id, name=m.name, points=points.get(m.id, 0))
                 for m in members],
        shifts=[
            ShiftIn(
                id=shift.id,
                starts_at=shift.starts_at,
                ends_at=shift.ends_at,
                weight=shift_type.weight,
                slots=shift.slots,
            )
            for shift, shift_type in open_shifts
        ],
        available={(member_id, shift_id)
                   for member_id, shift_id in available_rows},
    )


def to_proposal(problem: Problem, result: Result) -> Proposal:
    """Translate the solver's plain output into the API's response shape."""
    names = {m.id: m.name for m in problem.members}
    return Proposal(
        assignments=[
            ProposedAssignment(
                shift_id=shift_id, member_id=member_id, member_name=names[member_id])
            for shift_id, member_id in result.assignments
        ],
        unfilled=[
            UnfilledShift(shift_id=shift_id, missing=missing)
            for shift_id, missing in result.unfilled.items()
        ],
    )


@app.post("/api/clubs/{club_id}/schedule/generate")
def generate_schedule(club_id: int, session: SessionDep) -> Proposal:
    """Show what the solver would do. Saves nothing."""
    get_club_or_404(session, club_id)
    problem = build_problem(club_id, session)
    return to_proposal(problem, solve_greedy(problem))


@app.post("/api/clubs/{club_id}/schedule/publish")
def publish_schedule(club_id: int, session: SessionDep) -> Proposal:
    """Run the solver and save the result as assignments."""
    get_club_or_404(session, club_id)
    problem = build_problem(club_id, session)
    result = solve_greedy(problem)
    for shift_id, member_id in result.assignments:
        session.add(Assignment(shift_id=shift_id, member_id=member_id))
    session.commit()
    return to_proposal(problem, result)


@app.get("/api/clubs/{club_id}/assignments", response_model=list[AssignmentPublic])
def list_assignments(club_id: int, session: SessionDep) -> list[Assignment]:
    get_club_or_404(session, club_id)
    statement = (
        select(Assignment)
        .join(Shift, Assignment.shift_id == Shift.id)
        .where(Shift.club_id == club_id)
    )
    return list(session.exec(statement))
