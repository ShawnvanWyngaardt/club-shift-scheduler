"""'Try the demo': a private sandbox club for each visitor."""
from fastapi import APIRouter, HTTPException

import sandbox
from dependencies import SessionDep
from models import DemoClub, DemoMemberLink
from scheduling import points_by_member

router = APIRouter(prefix="/api/demo", tags=["demo"])


@router.post("", status_code=201)
def start_demo(session: SessionDep) -> DemoClub:
    """Give this visitor their own demo club. Demo clubs are removed after 24 hours."""
    sandbox.remove_expired_demos(session)
    if sandbox.demo_capacity_reached(session):
        raise HTTPException(
            status_code=503,
            detail="Too many demos are running right now. Please try again later.",
        )

    club, members = sandbox.create_demo_club(session)
    balances = points_by_member(club.id, session)
    return DemoClub(
        club_id=club.id,
        club_name=club.name,
        coordinator_token=club.coordinator_token,
        members=[
            DemoMemberLink(name=m.name, points=balances.get(m.id, 0), token=m.access_token)
            for m in members
        ],
    )
