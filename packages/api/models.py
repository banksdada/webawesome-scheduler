"""SQLModel data models for the Quick‑Stack API.

- `User` – minimal auth holder (email, hashed password placeholder).
- `Customer` – a business client.
- `Job` – scheduling entry, linked to a `Customer`.
"""

from typing import Optional
from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel, Relationship

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    # In a demo we store a plain‑text password; replace with a hash in prod.
    password: str

    # optional relationship to customers they own (not used now)
    customers: list["Customer"] = Relationship(back_populates="owner")

class Customer(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    owner_id: Optional[int] = Field(foreign_key="user.id")

    owner: Optional[User] = Relationship(back_populates="customers")
    jobs: list["Job"] = Relationship(back_populates="customer")

    # extra fields for the job‑management use case
    address: Optional[str] = None
    service_type: Optional[str] = None
    preferred_schedule: Optional[str] = None  # e.g., "Mon-Fri 9-5"

    # add notes about recurring jobs, etc.
    notes: Optional[str] = None

class Job(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: Optional[str] = None
    scheduled_at: Optional[str] = None  # iso‑datetime string for demo
    status: str = Field(default="pending")

    customer_id: int = Field(foreign_key="customer.id")
    customer: Customer = Relationship(back_populates="jobs")

    # technician assignment (can be null until assigned)
    technician_id: Optional[int] = Field(foreign_key="technician.id", default=None)
    technician: Optional["Technician"] = Relationship(back_populates="jobs")

    # scheduling preferences
    preferred_time: Optional[str] = None
    notes: Optional[str] = None

    # extra fields for quotes / invoicing
    price_estimate: Optional[float] = None
    deposit_paid: Optional[float] = None

class Technician(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: str = Field(index=True)
    phone: Optional[str] = None

    # relationship to jobs they handle
    jobs: list[Job] = Relationship(back_populates="technician")

    # skills / certifications (simple list as JSON)
    skills: Optional[list[str]] = Field(default=None, sa_column=Column(JSON))

    # availability schedule (simple JSON)
    availability: Optional[dict] = Field(default=None, sa_column=Column(JSON))