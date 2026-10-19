"""Database tables and the data shapes the API accepts and returns."""
import secrets
from datetime import datetime

from pydantic import model_validator
from sqlmodel import Field, SQLModel


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
