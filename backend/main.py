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
