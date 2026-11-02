"""Clubs and their setup: members, shift types and shifts."""

from datetime import timedelta

from fastapi import APIRouter, HTTPException
from sqlmodel import Session, select

from database import save
from dependencies import CoordinatorClub, SessionDep, get_club_or_404
from models import (
    Assignment,
    Availability,
    Club,
    ClubCreate,
    ClubPublic,
    ClubWithToken,
    Member,
    MemberCreate,
    MemberPublic,
    MemberWithToken,
    PointsEntry,
    Shift,
    ShiftCreate,
    ShiftDetail,
    ShiftPublic,
    ShiftType,
    ShiftTypeCreate,
    ShiftTypePublic,
    WeeklyShiftsCreate,
)
from sandbox import CLUB_TZ

router = APIRouter(prefix="/api/clubs", tags=["clubs"])


def find_in_club[T: (Member, Shift, ShiftType)](
    session: Session, model: type[T], item_id: int, club_id: int, label: str
) -> T:
    """Fetch a member, shift or shift type, but only if it belongs to this club."""
    item = session.get(model, item_id)
    if item is None or item.club_id != club_id:
        raise HTTPException(status_code=404, detail=f"{label} not found in this club")
    return item


@router.post("", response_model=ClubWithToken, status_code=201)
def create_club(data: ClubCreate, session: SessionDep) -> Club:
    return save(session, Club.model_validate(data))


@router.get("/{club_id}", response_model=ClubPublic)
def read_club(club_id: int, session: SessionDep) -> Club:
    return get_club_or_404(session, club_id)


@router.get("/{club_id}/coordinator", response_model=ClubPublic)
def check_coordinator_link(club: CoordinatorClub) -> Club:
    """Lets the coordinator screens confirm a link is valid before showing anything."""
    return club


@router.post("/{club_id}/members", response_model=MemberWithToken, status_code=201)
def add_member(
    club_id: int, data: MemberCreate, session: SessionDep, club: CoordinatorClub
) -> Member:
    return save(session, Member.model_validate(data, update={"club_id": club_id}))


@router.get("/{club_id}/members", response_model=list[MemberPublic])
def list_members(club_id: int, session: SessionDep) -> list[Member]:
    get_club_or_404(session, club_id)
    return list(session.exec(select(Member).where(Member.club_id == club_id)))


@router.get("/{club_id}/members/links", response_model=list[MemberWithToken])
def list_member_links(club_id: int, session: SessionDep, club: CoordinatorClub) -> list[Member]:
    """Every member with their personal link token. Coordinator only: tokens work like passwords."""
    statement = select(Member).where(Member.club_id == club_id).order_by(Member.name)
    return list(session.exec(statement))


@router.post("/{club_id}/shift-types", response_model=ShiftTypePublic, status_code=201)
def add_shift_type(
    club_id: int, data: ShiftTypeCreate, session: SessionDep, club: CoordinatorClub
) -> ShiftType:
    return save(session, ShiftType.model_validate(data, update={"club_id": club_id}))


@router.get("/{club_id}/shift-types", response_model=list[ShiftTypePublic])
def list_shift_types(club_id: int, session: SessionDep) -> list[ShiftType]:
    get_club_or_404(session, club_id)
    return list(session.exec(select(ShiftType).where(ShiftType.club_id == club_id)))


@router.post("/{club_id}/shifts", response_model=ShiftPublic, status_code=201)
def add_shift(club_id: int, data: ShiftCreate, session: SessionDep, club: CoordinatorClub) -> Shift:
    shift_type = session.get(ShiftType, data.shift_type_id)
    if shift_type is None or shift_type.club_id != club_id:
        raise HTTPException(status_code=404, detail="Shift type not found in this club")
    return save(session, Shift.model_validate(data, update={"club_id": club_id}))


@router.get("/{club_id}/shifts")
def list_shifts(club_id: int, session: SessionDep) -> list[ShiftDetail]:
    get_club_or_404(session, club_id)
    rows = session.exec(
        select(Shift, ShiftType)
        .where(Shift.club_id == club_id, Shift.shift_type_id == ShiftType.id)
        .order_by(Shift.starts_at)
    ).all()
    return [
        ShiftDetail(
            id=shift.id,
            shift_type_id=shift.shift_type_id,
            starts_at=shift.starts_at,
            ends_at=shift.ends_at,
            slots=shift.slots,
            shift_type=shift_type.name,
            weight=shift_type.weight,
        )
        for shift, shift_type in rows
    ]


@router.post("/{club_id}/shifts/weekly", response_model=list[ShiftPublic], status_code=201)
def add_weekly_shifts(
    club_id: int, data: WeeklyShiftsCreate, session: SessionDep, club: CoordinatorClub
) -> list[Shift]:
    find_in_club(session, ShiftType, data.shift_type_id, club_id, "Shift type")
    # Repeat in club time, so a 07:00 shift stays 07:00 after the clocks change.
    start = data.starts_at.astimezone(CLUB_TZ)
    end = data.ends_at.astimezone(CLUB_TZ)
    shifts = [
        Shift(
            club_id=club_id,
            shift_type_id=data.shift_type_id,
            starts_at=start + timedelta(weeks=week),
            ends_at=end + timedelta(weeks=week),
            slots=data.slots,
        )
        for week in range(data.weeks)
    ]
    session.add_all(shifts)
    session.commit()
    for shift in shifts:
        session.refresh(shift)
    return shifts


@router.delete("/{club_id}/members/{member_id}", status_code=204)
def remove_member(club_id: int, member_id: int, session: SessionDep, club: CoordinatorClub) -> None:
    member = find_in_club(session, Member, member_id, club_id, "Member")
    has_history = (
        session.exec(select(Assignment.id).where(Assignment.member_id == member_id)).first()
        or session.exec(select(PointsEntry.id).where(PointsEntry.member_id == member_id)).first()
    )
    if has_history:
        raise HTTPException(
            status_code=409,
            detail="This member has shifts or points on record, so they stay in the ledger",
        )
    for row in session.exec(select(Availability).where(Availability.member_id == member_id)):
        session.delete(row)
    session.flush()  # children first, then the member
    session.delete(member)
    session.commit()


@router.delete("/{club_id}/shifts/{shift_id}", status_code=204)
def remove_shift(club_id: int, shift_id: int, session: SessionDep, club: CoordinatorClub) -> None:
    shift = find_in_club(session, Shift, shift_id, club_id, "Shift")
    if session.exec(select(Assignment.id).where(Assignment.shift_id == shift_id)).first():
        raise HTTPException(status_code=409, detail="This shift is already scheduled")
    for row in session.exec(select(Availability).where(Availability.shift_id == shift_id)):
        session.delete(row)
    session.flush()
    session.delete(shift)
    session.commit()


@router.delete("/{club_id}/shift-types/{shift_type_id}", status_code=204)
def remove_shift_type(
    club_id: int, shift_type_id: int, session: SessionDep, club: CoordinatorClub
) -> None:
    shift_type = find_in_club(session, ShiftType, shift_type_id, club_id, "Shift type")
    if session.exec(select(Shift.id).where(Shift.shift_type_id == shift_type_id)).first():
        raise HTTPException(status_code=409, detail="Remove this type's shifts first")
    session.delete(shift_type)
    session.commit()
