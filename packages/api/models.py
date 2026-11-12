"""Database tables.

Everything belongs to an Organisation (one business using the tool).
A User is either an "admin" (office / owner) or a "technician" (does the jobs).
"""

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    """Current time in UTC, stored without a timezone label."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Organisation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    created_at: datetime = Field(default_factory=utcnow)


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    org_id: int = Field(foreign_key="organisation.id", index=True)
    email: str = Field(index=True, unique=True)
    name: str
    phone: Optional[str] = None
    role: str = "technician"  # "admin" or "technician"
    password_hash: str
    active: bool = True


class Customer(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    org_id: int = Field(foreign_key="organisation.id", index=True)
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None


class Job(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    org_id: int = Field(foreign_key="organisation.id", index=True)
    customer_id: int = Field(foreign_key="customer.id", index=True)
    title: str
    description: Optional[str] = None
    # pending -> assigned -> in_progress -> done   (or cancelled)
    status: str = "pending"
    scheduled_start: Optional[datetime] = Field(default=None, index=True)  # stored as UTC
    duration_minutes: int = 60
    assigned_to_id: Optional[int] = Field(default=None, foreign_key="user.id", index=True)
    price_estimate: Optional[float] = None
    notes: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=utcnow)
