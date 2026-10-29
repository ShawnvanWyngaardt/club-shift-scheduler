"""Shared request dependencies: the database session, lookups and access checks."""
import secrets
from typing import Annotated

from fastapi import Depends, Header, HTTPException
from sqlmodel import Session, select

from database import get_session
from models import Club, Member

SessionDep = Annotated[Session, Depends(get_session)]


def get_club_or_404(session: Session, club_id: int) -> Club:
    """Fetch a club, or stop the request with a 404."""
    club = session.get(Club, club_id)
    if club is None:
        raise HTTPException(status_code=404, detail="Club not found")
    return club


def check_coordinator(club: Club, token: str) -> None:
    """Stop the request unless the token belongs to this club's coordinator."""
    if not secrets.compare_digest(club.coordinator_token, token):
        raise HTTPException(status_code=403, detail="Not the coordinator of this club")


def require_coordinator(
    club_id: int,
    session: SessionDep,
    x_coordinator_token: Annotated[str, Header()],
) -> Club:
    club = get_club_or_404(session, club_id)
    check_coordinator(club, x_coordinator_token)
    return club


CoordinatorClub = Annotated[Club, Depends(require_coordinator)]


def get_member_by_token(token: str, session: Session) -> Member:
    """Find the member behind a personal link, or stop with a 404."""
    member = session.exec(select(Member).where(Member.access_token == token)).first()
    if member is None:
        raise HTTPException(status_code=404, detail="Unknown link")
    return member
