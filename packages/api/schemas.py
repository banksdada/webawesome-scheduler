"""What the API accepts and returns."""

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_serializer, field_validator


def to_utc_naive(value: Optional[datetime]) -> Optional[datetime]:
    """Dates are stored as UTC without a timezone label."""
    if value is None:
        return None
    if value.tzinfo is not None:
        value = value.astimezone(timezone.utc).replace(tzinfo=None)
    return value


# ---------- accounts ----------
class SignupIn(BaseModel):
    organisation_name: str = Field(min_length=1, max_length=120)
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    name: str


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    phone: Optional[str] = None
    role: str
    active: bool


class TeamIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    phone: Optional[str] = None
    password: str = Field(min_length=8, max_length=72)
    role: str = "technician"

    @field_validator("role")
    @classmethod
    def _role(cls, v: str) -> str:
        if v not in ("technician", "admin"):
            raise ValueError("role must be 'technician' or 'admin'")
        return v


class TeamPatch(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    active: Optional[bool] = None


# ---------- customers ----------
class CustomerIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None


class CustomerPatch(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None


# ---------- jobs ----------
class JobIn(BaseModel):
    customer_id: int
    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = None
    scheduled_start: Optional[datetime] = None
    duration_minutes: int = Field(default=60, ge=5, le=24 * 60)
    assigned_to_id: Optional[int] = None
    price_estimate: Optional[float] = Field(default=None, ge=0)
    notes: Optional[str] = None
    allow_overlap: bool = False


class JobPatch(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = None
    scheduled_start: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(default=None, ge=5, le=24 * 60)
    assigned_to_id: Optional[int] = None
    price_estimate: Optional[float] = Field(default=None, ge=0)
    notes: Optional[str] = None
    status: Optional[str] = None  # only "cancelled" is accepted here
    allow_overlap: bool = False


class PersonBrief(BaseModel):
    id: int
    name: str
    phone: Optional[str] = None


class CustomerBrief(PersonBrief):
    address: Optional[str] = None


class JobOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    status: str
    scheduled_start: Optional[datetime] = None
    duration_minutes: int
    price_estimate: Optional[float] = None
    notes: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    customer: CustomerBrief
    assigned_to: Optional[PersonBrief] = None

    # Send dates with a "Z" so browsers know they are UTC
    @field_serializer("scheduled_start", "started_at", "completed_at")
    def _utc(self, v: Optional[datetime]):
        return v.isoformat() + "Z" if v else None
