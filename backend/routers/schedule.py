"""Generating, publishing and listing a club's schedule."""

from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from database import save
from dependencies import CoordinatorClub, SessionDep
from models import (
    Assignment,
    AssignmentDetail,
    AssignmentMove,
    AssignmentPublic,
    Candidate,
    Member,
    Proposal,
    Shift,
    ShiftType,
)
from scheduling import build_problem, busy_member_ids, candidates_for, to_proposal
from solver import solve_greedy

router = APIRouter(prefix="/api/clubs/{club_id}", tags=["schedule"])


@router.post("/schedule/generate")
def generate_schedule(club_id: int, session: SessionDep, club: CoordinatorClub) -> Proposal:
    """Show what the solver would do. Saves nothing."""
    problem = build_problem(club_id, session)
    return to_proposal(problem, solve_greedy(problem))


@router.post("/schedule/publish")
def publish_schedule(club_id: int, session: SessionDep, club: CoordinatorClub) -> Proposal:
    """Run the solver and save the result as assignments."""
    problem = build_problem(club_id, session)
    result = solve_greedy(problem)
    for shift_id, member_id in result.assignments:
        session.add(Assignment(shift_id=shift_id, member_id=member_id))
    session.commit()
    return to_proposal(problem, result)


@router.get("/assignments")
def list_assignments(
    club_id: int, session: SessionDep, club: CoordinatorClub
) -> list[AssignmentDetail]:
    rows = session.exec(
        select(Assignment, Member, Shift, ShiftType)
        .where(
            Assignment.member_id == Member.id,
            Assignment.shift_id == Shift.id,
            Shift.shift_type_id == ShiftType.id,
            Shift.club_id == club_id,
        )
        .order_by(Shift.starts_at)
    ).all()
    return [
        AssignmentDetail(
            id=assignment.id,
            shift_id=assignment.shift_id,
            member_id=assignment.member_id,
            status=assignment.status,
            member_name=member.name,
            shift_type=shift_type.name,
            starts_at=shift.starts_at,
            ends_at=shift.ends_at,
            weight=shift_type.weight,
        )
        for assignment, member, shift, shift_type in rows
    ]


def get_shift_in_club(session: SessionDep, club_id: int, shift_id: int) -> Shift:
    shift = session.get(Shift, shift_id)
    if shift is None or shift.club_id != club_id:
        raise HTTPException(status_code=404, detail="Shift not found in this club")
    return shift


@router.get("/shifts/{shift_id}/candidates")
def open_slot_candidates(
    club_id: int, shift_id: int, session: SessionDep, club: CoordinatorClub
) -> list[Candidate]:
    """Who could fill an empty slot on this shift."""
    return candidates_for(session, get_shift_in_club(session, club_id, shift_id))


@router.post("/shifts/{shift_id}/assignments", response_model=AssignmentPublic, status_code=201)
def assign_by_hand(
    club_id: int, shift_id: int, data: AssignmentMove, session: SessionDep, club: CoordinatorClub
) -> Assignment:
    """The coordinator fills an empty slot, for example after asking around in the club chat."""
    shift = get_shift_in_club(session, club_id, shift_id)
    if shift.starts_at <= datetime.now(UTC):
        raise HTTPException(status_code=409, detail="This shift has already started")
    taken = session.exec(
        select(func.count()).select_from(Assignment).where(Assignment.shift_id == shift.id)
    ).one()
    if taken >= shift.slots:
        raise HTTPException(status_code=409, detail="This shift is already full")

    member = session.get(Member, data.member_id)
    if member is None or member.club_id != club_id:
        raise HTTPException(status_code=404, detail="Member not found in this club")
    if member.id in busy_member_ids(session, shift):
        raise HTTPException(
            status_code=409, detail=f"{member.name} is already on a shift at that time"
        )
    return save(session, Assignment(shift_id=shift.id, member_id=member.id))
