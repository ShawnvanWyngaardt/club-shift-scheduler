"""The bridge between the database and the solver: rows in, plain data out, and back again."""

from dataclasses import replace
from datetime import UTC, datetime

from sqlmodel import Session, col, func, select

from models import (
    Assignment,
    Availability,
    Balance,
    Ledger,
    Member,
    PointsEntry,
    PointsEntryPublic,
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
    Only upcoming shifts with empty slots are scheduled; existing assignments are kept."""
    now = datetime.now(UTC)
    members = session.exec(select(Member).where(Member.club_id == club_id)).all()
    points = points_by_member(club_id, session)

    upcoming = session.exec(
        select(Shift, ShiftType).where(
            Shift.club_id == club_id,
            Shift.shift_type_id == ShiftType.id,
            col(Shift.starts_at) > now,
        )
    ).all()
    shift_in = {
        shift.id: ShiftIn(
            id=shift.id,
            starts_at=shift.starts_at,
            ends_at=shift.ends_at,
            weight=shift_type.weight,
            slots=shift.slots,
        )
        for shift, shift_type in upcoming
    }

    # Who already holds which upcoming shift, from earlier publishes.
    held = session.exec(
        select(Assignment.member_id, Assignment.shift_id).where(
            col(Assignment.shift_id).in_(list(shift_in))
        )
    ).all()
    filled: dict[int, int] = {}
    already_assigned: dict[int, list[ShiftIn]] = {}
    for member_id, shift_id in held:
        filled[shift_id] = filled.get(shift_id, 0) + 1
        already_assigned.setdefault(member_id, []).append(shift_in[shift_id])

    # Only the empty slots are left to fill.
    open_shifts = [
        replace(shift, slots=shift.slots - filled.get(shift.id, 0))
        for shift in shift_in.values()
        if shift.slots > filled.get(shift.id, 0)
    ]
    available_rows = session.exec(
        select(Availability.member_id, Availability.shift_id).where(
            col(Availability.shift_id).in_([shift.id for shift in open_shifts])
        )
    ).all()

    return Problem(
        members=[MemberIn(id=m.id, name=m.name, points=points.get(m.id, 0)) for m in members],
        shifts=open_shifts,
        available={(member_id, shift_id) for member_id, shift_id in available_rows},
        already_assigned=already_assigned,
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


def build_ledger(club_id: int, session: Session, member_id: int | None = None) -> Ledger:
    """Every member's balance, plus the history behind it, newest first.

    With a member_id, the history is only that member's: members see everyone's
    balance, but not each other's no-shows.
    """
    points = points_by_member(club_id, session)
    members = session.exec(
        select(Member).where(Member.club_id == club_id).order_by(Member.name)
    ).all()
    query = (
        select(PointsEntry)
        .join(Member, PointsEntry.member_id == Member.id)
        .where(Member.club_id == club_id)
    )
    if member_id is not None:
        query = query.where(PointsEntry.member_id == member_id)
    entries = session.exec(query.order_by(col(PointsEntry.created_at).desc())).all()
    return Ledger(
        balances=[
            Balance(member_id=m.id, name=m.name, balance=points.get(m.id, 0)) for m in members
        ],
        entries=[PointsEntryPublic.model_validate(e) for e in entries],
    )
