"""Clubs and their setup: members, shift types and shifts."""
from fastapi import APIRouter, HTTPException
from sqlmodel import select

from database import save
from dependencies import CoordinatorClub, SessionDep, get_club_or_404
from models import (
    Club,
    ClubCreate,
    ClubPublic,
    ClubWithToken,
    Member,
    MemberCreate,
    MemberPublic,
    MemberWithToken,
    Shift,
    ShiftCreate,
    ShiftDetail,
    ShiftPublic,
    ShiftType,
    ShiftTypeCreate,
    ShiftTypePublic,
)

router = APIRouter(prefix="/api/clubs", tags=["clubs"])


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
    statement = select(Member).where(
        Member.club_id == club_id).order_by(Member.name)
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
def add_shift(
    club_id: int, data: ShiftCreate, session: SessionDep, club: CoordinatorClub
) -> Shift:
    shift_type = session.get(ShiftType, data.shift_type_id)
    if shift_type is None or shift_type.club_id != club_id:
        raise HTTPException(
            status_code=404, detail="Shift type not found in this club")
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
