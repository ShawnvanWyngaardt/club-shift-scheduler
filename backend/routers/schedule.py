"""Generating, publishing and listing a club's schedule."""
from fastapi import APIRouter
from sqlmodel import select

from dependencies import CoordinatorClub, SessionDep, get_club_or_404
from models import Assignment, AssignmentDetail, Member, Proposal, Shift, ShiftType
from scheduling import build_problem, to_proposal
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
def list_assignments(club_id: int, session: SessionDep) -> list[AssignmentDetail]:
    get_club_or_404(session, club_id)
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
