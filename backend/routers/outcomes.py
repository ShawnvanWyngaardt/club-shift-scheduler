"""Changing assignments after publishing, recording outcomes, and the points ledger."""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Header, HTTPException
from sqlmodel import Session, select

from dependencies import CoordinatorClub, SessionDep, check_coordinator
from models import (
    Assignment,
    AssignmentMove,
    AssignmentPublic,
    AssignmentUpdate,
    Availability,
    Candidate,
    Club,
    Ledger,
    Member,
    PointsEntry,
    Shift,
    ShiftType,
)
from scheduling import build_ledger, busy_member_ids, candidates_for

router = APIRouter(prefix="/api", tags=["outcomes"])

CoordinatorToken = Annotated[str, Header()]


def load_assignment(
    session: Session, assignment_id: int, token: str
) -> tuple[Assignment, Shift, ShiftType, Club]:
    """Fetch an assignment with its shift, type and club, for this club's coordinator only."""
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
    check_coordinator(club, token)
    return assignment, shift, shift_type, club


def require_changeable(assignment: Assignment, shift: Shift) -> None:
    """Only assignments without an outcome, on shifts that haven't started, can change."""
    if assignment.status != "assigned":
        raise HTTPException(
            status_code=409,
            detail=f"Already marked as {assignment.status}, so it can't be changed",
        )
    if shift.starts_at <= datetime.now(UTC):
        raise HTTPException(status_code=409, detail="This shift has already started")


def clear_answer(session: Session, member_id: int, shift_id: int) -> None:
    """Untick a member's 'I could do this' for one shift, if they had ticked it."""
    answer = session.get(Availability, {"member_id": member_id, "shift_id": shift_id})
    if answer is not None:
        session.delete(answer)


@router.patch("/assignments/{assignment_id}", response_model=AssignmentPublic)
def record_outcome(
    assignment_id: int,
    data: AssignmentUpdate,
    session: SessionDep,
    x_coordinator_token: CoordinatorToken,
) -> Assignment:
    """Mark an assignment done or no-show, and write the matching ledger entry."""
    assignment, shift, shift_type, _ = load_assignment(session, assignment_id, x_coordinator_token)
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


@router.delete("/assignments/{assignment_id}", status_code=204)
def unassign(
    assignment_id: int, session: SessionDep, x_coordinator_token: CoordinatorToken
) -> None:
    """Take a member off an upcoming shift. The slot is open again for the next refill."""
    assignment, shift, _, _ = load_assignment(session, assignment_id, x_coordinator_token)
    require_changeable(assignment, shift)
    # Without this, the next refill would pick the same member straight back.
    clear_answer(session, assignment.member_id, shift.id)
    session.delete(assignment)
    session.commit()


@router.get("/assignments/{assignment_id}/candidates")
def list_candidates(
    assignment_id: int, session: SessionDep, x_coordinator_token: CoordinatorToken
) -> list[Candidate]:
    """Who could take this shift instead: free members who said yes first, fewest points on top."""
    assignment, shift, _, _ = load_assignment(session, assignment_id, x_coordinator_token)
    return candidates_for(session, shift, exclude_member_id=assignment.member_id)


@router.put("/assignments/{assignment_id}/member", response_model=AssignmentPublic)
def reassign(
    assignment_id: int,
    data: AssignmentMove,
    session: SessionDep,
    x_coordinator_token: CoordinatorToken,
) -> Assignment:
    """Give an upcoming shift to another member of the same club."""
    assignment, shift, _, club = load_assignment(session, assignment_id, x_coordinator_token)
    require_changeable(assignment, shift)

    member = session.get(Member, data.member_id)
    if member is None or member.club_id != club.id:
        raise HTTPException(status_code=404, detail="Member not found in this club")
    if member.id in busy_member_ids(session, shift):
        raise HTTPException(
            status_code=409, detail=f"{member.name} is already on a shift at that time"
        )

    clear_answer(session, assignment.member_id, shift.id)
    assignment.member_id = member.id
    session.add(assignment)
    session.commit()
    session.refresh(assignment)
    return assignment


@router.get("/clubs/{club_id}/ledger")
def read_ledger(club_id: int, session: SessionDep, club: CoordinatorClub) -> Ledger:
    """Every member's balance and the club's full history. Coordinator only."""
    return build_ledger(club_id, session)
