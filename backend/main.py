"""API entry point for the Club Shift Scheduler."""
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from sqlmodel import Session, select

from database import create_tables, get_session
from models import (
    Club,
    ClubCreate,
    ClubPublic,
    ClubWithToken,
    Health,
    Member,
    MemberCreate,
    MemberPublic,
    MemberWithToken,
    Shift,
    ShiftCreate,
    ShiftPublic,
    ShiftType,
    ShiftTypeCreate,
    ShiftTypePublic,
)


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
