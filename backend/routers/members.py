"""Everything a member does through their personal link."""
from fastapi import APIRouter, HTTPException
from sqlmodel import Session, select

from dependencies import SessionDep, get_member_by_token
from models import (
    Assignment,
    Availability,
    AvailabilityUpdate,
    Club,
    Member,
    MemberProfile,
    MyShift,
    Shift,
    ShiftType,
)
from scheduling import points_by_member

router = APIRouter(prefix="/api/me", tags=["member link"])


def my_shifts(member: Member, session: Session) -> list[MyShift]:
    """All shifts in the member's club, with their availability and assignments."""
    rows = session.exec(
        select(Shift, ShiftType)
        .where(Shift.club_id == member.club_id, Shift.shift_type_id == ShiftType.id)
        .order_by(Shift.starts_at)
    ).all()
    chosen = set(
        session.exec(select(Availability.shift_id).where(Availability.member_id == member.id)).all()
    )
    assigned = set(
        session.exec(select(Assignment.shift_id).where(Assignment.member_id == member.id)).all()
    )
    return [
        MyShift(
            id=shift.id,
            shift_type=shift_type.name,
            weight=shift_type.weight,
            starts_at=shift.starts_at,
            ends_at=shift.ends_at,
            available=shift.id in chosen,
            assigned=shift.id in assigned,
        )
        for shift, shift_type in rows
    ]


@router.get("/{token}")
def read_me(token: str, session: SessionDep) -> MemberProfile:
    """Who the link belongs to, and their balance this season."""
    member = get_member_by_token(token, session)
    club = session.get(Club, member.club_id)
    balance = points_by_member(member.club_id, session).get(member.id, 0)
    return MemberProfile(name=member.name, club_id=club.id, club_name=club.name, balance=balance)


@router.get("/{token}/shifts", response_model=list[MyShift])
def read_my_shifts(token: str, session: SessionDep) -> list[MyShift]:
    member = get_member_by_token(token, session)
    return my_shifts(member, session)


@router.put("/{token}/availability", response_model=list[MyShift])
def update_my_availability(
    token: str, data: AvailabilityUpdate, session: SessionDep
) -> list[MyShift]:
    member = get_member_by_token(token, session)

    club_shift_ids = set(
        session.exec(select(Shift.id).where(Shift.club_id == member.club_id)).all()
    )
    unknown = set(data.shift_ids) - club_shift_ids
    if unknown:
        raise HTTPException(status_code=422, detail=f"Not shifts in your club: {sorted(unknown)}")

    assigned = set(
        session.exec(select(Assignment.shift_id).where(Assignment.member_id == member.id)).all()
    )
    dropped = assigned - set(data.shift_ids)
    if dropped:
        raise HTTPException(
            status_code=409,
            detail=f"Already assigned to you, ask your coordinator to swap: {sorted(dropped)}",
        )

    # Replace the member's answers completely: remove the old ones, then add the new ones.
    for old in session.exec(select(Availability).where(Availability.member_id == member.id)).all():
        session.delete(old)
    session.flush()
    for shift_id in set(data.shift_ids):
        session.add(Availability(member_id=member.id, shift_id=shift_id))
    session.commit()

    return my_shifts(member, session)
