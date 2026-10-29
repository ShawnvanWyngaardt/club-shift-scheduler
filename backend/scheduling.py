"""The bridge between the database and the solver: rows in, plain data out, and back again."""
from sqlmodel import Session, col, func, select

from models import (
    Assignment,
    Availability,
    Member,
    PointsEntry,
    Proposal,
    ProposedAssignment,
    Shift,
    ShiftType,
    UnfilledShift,
)
from solver import MemberIn, Problem, Result, ShiftIn


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
    members = session.exec(select(Member).where(Member.club_id == club_id)).all()
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
        members=[MemberIn(id=m.id, name=m.name, points=points.get(m.id, 0)) for m in members],
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
        available={(member_id, shift_id) for member_id, shift_id in available_rows},
    )


def to_proposal(problem: Problem, result: Result) -> Proposal:
    """Translate the solver's plain output into the API's response shape."""
    names = {m.id: m.name for m in problem.members}
    return Proposal(
        assignments=[
            ProposedAssignment(shift_id=shift_id, member_id=member_id, member_name=names[member_id])
            for shift_id, member_id in result.assignments
        ],
        unfilled=[
            UnfilledShift(shift_id=shift_id, missing=missing)
            for shift_id, missing in result.unfilled.items()
        ],
    )
