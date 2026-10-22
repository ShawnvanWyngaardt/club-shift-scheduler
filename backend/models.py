"""Database tables and the data shapes the API accepts and returns."""
import secrets
from datetime import datetime, timezone

from pydantic import model_validator
from sqlmodel import Field, SQLModel
from typing import Literal


def new_token() -> str:
    """Return a random, URL-safe secret for personal links."""
    return secrets.token_urlsafe(16)


class Health(SQLModel):
    status: str


# ---------- Club ----------
class ClubCreate(SQLModel):
    name: str = Field(min_length=1, max_length=100)


class Club(ClubCreate, table=True):
    id: int | None = Field(default=None, primary_key=True)
    coordinator_token: str = Field(default_factory=new_token, index=True)


class ClubPublic(ClubCreate):
    id: int


class ClubWithToken(ClubPublic):
    coordinator_token: str


# ---------- Member ----------
class MemberCreate(SQLModel):
    name: str = Field(min_length=1, max_length=100)


class Member(MemberCreate, table=True):
    id: int | None = Field(default=None, primary_key=True)
    club_id: int = Field(foreign_key="club.id", index=True)
    access_token: str = Field(default_factory=new_token, index=True)


class MemberPublic(MemberCreate):
    id: int


class MemberWithToken(MemberPublic):
    access_token: str


# ---------- Shift type ----------
class ShiftTypeCreate(SQLModel):
    name: str = Field(min_length=1, max_length=100)
    weight: int = Field(ge=1, le=3)


class ShiftType(ShiftTypeCreate, table=True):
    id: int | None = Field(default=None, primary_key=True)
    club_id: int = Field(foreign_key="club.id", index=True)


class ShiftTypePublic(ShiftTypeCreate):
    id: int


# ---------- Shift ----------
class ShiftBase(SQLModel):
    starts_at: datetime
    ends_at: datetime
    slots: int = Field(ge=1, le=50)


class ShiftCreate(ShiftBase):
    shift_type_id: int

    @model_validator(mode="after")
    def check_times(self) -> "ShiftCreate":
        if self.ends_at <= self.starts_at:
            raise ValueError("ends_at must be after starts_at")
        return self


class Shift(ShiftBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    club_id: int = Field(foreign_key="club.id", index=True)
    shift_type_id: int = Field(foreign_key="shifttype.id", index=True)


class ShiftPublic(ShiftBase):
    id: int
    shift_type_id: int


# ---------- Availability ----------
class Availability(SQLModel, table=True):
    """One row means: this member can do this shift. No row means unavailable."""
    member_id: int = Field(foreign_key="member.id", primary_key=True)
    shift_id: int = Field(foreign_key="shift.id", primary_key=True)


class AvailabilityUpdate(SQLModel):
    shift_ids: list[int]


class MyShift(SQLModel):
    """A shift as one member sees it, with their own answer."""
    id: int
    shift_type: str
    starts_at: datetime
    ends_at: datetime
    available: bool


# ---------- Assignments and points ----------
class Assignment(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    shift_id: int | None = Field(foreign_key="shift.id", index=True)
    member_id: int | None = Field(foreign_key="member.id", index=True)
    status: str = Field(default="assigned")  # assigned, done, no_show


class AssignmentPublic(SQLModel):
    id: int
    shift_id: int
    member_id: int
    status: str


class PointsEntry(SQLModel, table=True):
    """Append-only ledger: a member's balance is the sum of their entries."""
    id: int | None = Field(default=None, primary_key=True)
    member_id: int = Field(foreign_key="member.id", index=True)
    change: int
    reason: str = Field(max_length=200)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ---------- Schedule proposal ----------
class ProposedAssignment(SQLModel):
    shift_id: int
    member_id: int
    member_name: str


class UnfilledShift(SQLModel):
    shift_id: int
    missing: int


class Proposal(SQLModel):
    assignments: list[ProposedAssignment]
    unfilled: list[UnfilledShift]


# ---------- Outcomes and ledger ----------
class AssignmentUpdate(SQLModel):
    status: Literal["done", "no_show"]


class Balance(SQLModel):
    member_id: int
    name: str
    balance: int


class PointsEntryPublic(SQLModel):
    member_id: int
    change: int
    reason: str
    created_at: datetime


class Ledger(SQLModel):
    balances: list[Balance]
    entries: list[PointsEntryPublic]
