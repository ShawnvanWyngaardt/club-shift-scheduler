"""Recording what happened on the day, and the points ledger it feeds."""
from typing import Annotated

from fastapi import APIRouter, Header, HTTPException
from sqlmodel import col, select

from dependencies import SessionDep, check_coordinator, get_club_or_404
from models import (
    Assignment,
    AssignmentPublic,
    AssignmentUpdate,
    Balance,
    Club,
    Ledger,
    Member,
    PointsEntry,
    PointsEntryPublic,
    Shift,
    ShiftType,
)
from scheduling import points_by_member

router = APIRouter(prefix="/api", tags=["outcomes"])


@router.patch("/assignments/{assignment_id}", response_model=AssignmentPublic)
def record_outcome(
    assignment_id: int,
    data: AssignmentUpdate,
    session: SessionDep,
    x_coordinator_token: Annotated[str, Header()],
) -> Assignment:
    """Mark an assignment done or no-show, and write the matching ledger entry."""
    assignment = session.get(Assignment, assignment_id)
    if assignment is None:
        raise HTTPException(status_code=404, detail="Assignment not found")

    shift, shift_type, club = session.exec(
        select(Shift, ShiftType, Club).where(
            Shift.id == assignment.shift_id,
            Shift.shift_type_id == ShiftType.id,
            Club.id == Shift.club_id,
        )
    ).one()
    check_coordinator(club, x_coordinator_token)

    if assignment.status != "assigned":
        raise HTTPException(status_code=409, detail=f"Already marked as {assignment.status}")

    change = shift_type.weight if data.status == "done" else -shift_type.weight
    assignment.status = data.status
    session.add(assignment)
    session.add(
        PointsEntry(
            member_id=assignment.member_id,
            change=change,
            reason=f"{data.status}: {shift_type.name}, {shift.starts_at:%a %d %b}",
        )
    )
    session.commit()  # status and ledger entry are saved together, or not at all
    session.refresh(assignment)
    return assignment


@router.get("/clubs/{club_id}/ledger")
def read_ledger(club_id: int, session: SessionDep) -> Ledger:
    """Every member's balance, plus the history behind it, newest first."""
    get_club_or_404(session, club_id)
    points = points_by_member(club_id, session)
    members = session.exec(
        select(Member).where(Member.club_id == club_id).order_by(Member.name)
    ).all()
    entries = session.exec(
        select(PointsEntry)
        .join(Member, PointsEntry.member_id == Member.id)
        .where(Member.club_id == club_id)
        .order_by(col(PointsEntry.created_at).desc())
    ).all()
    return Ledger(
        balances=[
            Balance(member_id=m.id, name=m.name, balance=points.get(m.id, 0)) for m in members
        ],
        entries=[PointsEntryPublic.model_validate(e) for e in entries],
    )
