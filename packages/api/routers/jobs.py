"""Jobs: create, schedule, assign (dispatch), and work through start -> complete."""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlmodel import Session, select

from .. import models, notify
from ..db import get_session
from ..deps import get_current_user, require_admin
from ..schemas import CustomerBrief, JobIn, JobOut, JobPatch, PersonBrief, to_utc_naive

router = APIRouter(prefix="/jobs", tags=["jobs"])

OPEN_STATUSES = ("pending", "assigned", "in_progress")


# ---------------------------------------------------------------- helpers
def _job_out(job: models.Job, customers: dict, users: dict) -> JobOut:
    c = customers[job.customer_id]
    tech = users.get(job.assigned_to_id) if job.assigned_to_id else None
    return JobOut(
        **job.model_dump(),
        customer=CustomerBrief(id=c.id, name=c.name, phone=c.phone, address=c.address),
        assigned_to=PersonBrief(id=tech.id, name=tech.name, phone=tech.phone) if tech else None,
    )


def _outs(session: Session, jobs: list[models.Job]) -> list[JobOut]:
    cust_ids = {j.customer_id for j in jobs}
    user_ids = {j.assigned_to_id for j in jobs if j.assigned_to_id}
    customers, users = {}, {}
    if cust_ids:
        customers = {c.id: c for c in session.exec(select(models.Customer).where(models.Customer.id.in_(cust_ids)))}
    if user_ids:
        users = {u.id: u for u in session.exec(select(models.User).where(models.User.id.in_(user_ids)))}
    return [_job_out(j, customers, users) for j in jobs]


def _own_customer(session: Session, org_id: int, customer_id: int) -> models.Customer:
    customer = session.get(models.Customer, customer_id)
    if not customer or customer.org_id != org_id:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


def _own_user(session: Session, org_id: int, user_id: int) -> models.User:
    user = session.get(models.User, user_id)
    if not user or user.org_id != org_id or not user.active:
        raise HTTPException(status_code=404, detail="Technician not found")
    return user


def _clashes(session: Session, org_id: int, tech_id: int, start: datetime, minutes: int, ignore_job_id: Optional[int] = None):
    """Jobs for this technician that overlap the given time slot."""
    end = start + timedelta(minutes=minutes)
    stmt = select(models.Job).where(
        models.Job.org_id == org_id,
        models.Job.assigned_to_id == tech_id,
        models.Job.status.in_(OPEN_STATUSES),
        models.Job.scheduled_start != None,  # noqa: E711  (SQL "is not null")
        models.Job.scheduled_start < end,
    )
    found = []
    for other in session.exec(stmt):
        if ignore_job_id is not None and other.id == ignore_job_id:
            continue
        if other.scheduled_start + timedelta(minutes=other.duration_minutes) > start:
            found.append(other)
    return found


def _raise_if_clash(session, org_id, tech_id, start, minutes, allow, ignore_job_id=None):
    if allow or tech_id is None or start is None:
        return
    clashes = _clashes(session, org_id, tech_id, start, minutes, ignore_job_id)
    if clashes:
        raise HTTPException(
            status_code=409,
            detail={
                "message": "This technician already has a job at that time",
                "conflicts": [
                    {"id": c.id, "title": c.title, "scheduled_start": c.scheduled_start.isoformat() + "Z"} for c in clashes
                ],
            },
        )


def _queue_assignment_email(background: BackgroundTasks, job: models.Job, tech: models.User, customer: models.Customer):
    background.add_task(
        notify.job_assigned,
        {
            "tech_name": tech.name,
            "tech_email": tech.email,
            "title": job.title,
            "scheduled_start": job.scheduled_start,
            "duration_minutes": job.duration_minutes,
            "customer_name": customer.name,
            "address": customer.address,
            "customer_phone": customer.phone,
            "notes": job.notes,
        },
    )


def _visible_job(session: Session, user: models.User, job_id: int) -> models.Job:
    """Admins see every job in their business; technicians only their own."""
    job = session.get(models.Job, job_id)
    if not job or job.org_id != user.org_id:
        raise HTTPException(status_code=404, detail="Not found")
    if user.role != "admin" and job.assigned_to_id != user.id:
        raise HTTPException(status_code=404, detail="Not found")
    return job


# ---------------------------------------------------------------- routes
@router.post("", response_model=JobOut)
def create_job(
    body: JobIn, background: BackgroundTasks, admin: models.User = Depends(require_admin), session: Session = Depends(get_session)
):
    customer = _own_customer(session, admin.org_id, body.customer_id)
    start = to_utc_naive(body.scheduled_start)
    tech = _own_user(session, admin.org_id, body.assigned_to_id) if body.assigned_to_id else None
    _raise_if_clash(session, admin.org_id, tech.id if tech else None, start, body.duration_minutes, body.allow_overlap)

    job = models.Job(
        org_id=admin.org_id,
        customer_id=customer.id,
        title=body.title.strip(),
        description=body.description,
        scheduled_start=start,
        duration_minutes=body.duration_minutes,
        assigned_to_id=tech.id if tech else None,
        status="assigned" if tech else "pending",
        price_estimate=body.price_estimate,
        notes=body.notes,
    )
    session.add(job)
    session.commit()
    session.refresh(job)
    if tech:
        _queue_assignment_email(background, job, tech, customer)
    return _outs(session, [job])[0]


@router.get("", response_model=list[JobOut])
def list_jobs(
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    assigned_to_id: Optional[int] = None,
    unscheduled: bool = False,
    user: models.User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Jobs between start and end. unscheduled=true returns open jobs that have no time yet."""
    stmt = select(models.Job).where(models.Job.org_id == user.org_id)
    if user.role != "admin":
        stmt = stmt.where(models.Job.assigned_to_id == user.id)
    elif assigned_to_id is not None:
        stmt = stmt.where(models.Job.assigned_to_id == assigned_to_id)
    if unscheduled:
        stmt = stmt.where(models.Job.scheduled_start == None, models.Job.status.in_(OPEN_STATUSES))  # noqa: E711
    else:
        if start is not None:
            stmt = stmt.where(models.Job.scheduled_start >= to_utc_naive(start))
        if end is not None:
            stmt = stmt.where(models.Job.scheduled_start < to_utc_naive(end))
    jobs = session.exec(stmt.order_by(models.Job.scheduled_start, models.Job.id)).all()
    return _outs(session, list(jobs))


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: int, user: models.User = Depends(get_current_user), session: Session = Depends(get_session)):
    return _outs(session, [_visible_job(session, user, job_id)])[0]


@router.patch("/{job_id}", response_model=JobOut)
def update_job(
    job_id: int,
    body: JobPatch,
    background: BackgroundTasks,
    admin: models.User = Depends(require_admin),
    session: Session = Depends(get_session),
):
    job = _visible_job(session, admin, job_id)
    changes = body.model_dump(exclude_unset=True)
    changes.pop("allow_overlap", None)

    if "status" in changes:
        if changes["status"] != "cancelled":
            raise HTTPException(status_code=422, detail="status can only be set to 'cancelled' here")
        if job.status == "done":
            raise HTTPException(status_code=409, detail="A finished job cannot be cancelled")
        job.status = "cancelled"
        changes.pop("status")
    elif job.status in ("done", "cancelled") and (
        "scheduled_start" in changes or "assigned_to_id" in changes or "duration_minutes" in changes
    ):
        raise HTTPException(status_code=409, detail=f"A {job.status} job cannot be rescheduled or reassigned")

    new_tech_id = changes.get("assigned_to_id", job.assigned_to_id)
    new_start = to_utc_naive(changes["scheduled_start"]) if "scheduled_start" in changes else job.scheduled_start
    new_minutes = changes.get("duration_minutes") or job.duration_minutes
    tech = _own_user(session, admin.org_id, new_tech_id) if new_tech_id else None

    if job.status != "cancelled":
        _raise_if_clash(session, admin.org_id, new_tech_id, new_start, new_minutes, body.allow_overlap, ignore_job_id=job.id)

    tech_changed = new_tech_id != job.assigned_to_id
    time_changed = new_start != job.scheduled_start

    for key in ("title", "description", "price_estimate", "notes"):
        if key in changes and (changes[key] is not None or key != "title"):
            setattr(job, key, changes[key])
    if "duration_minutes" in changes and changes["duration_minutes"]:
        job.duration_minutes = changes["duration_minutes"]
    job.scheduled_start = new_start
    job.assigned_to_id = new_tech_id

    if job.status in ("pending", "assigned"):
        job.status = "assigned" if new_tech_id else "pending"

    session.add(job)
    session.commit()
    session.refresh(job)

    if tech and job.status in ("assigned", "in_progress") and (tech_changed or time_changed):
        _queue_assignment_email(background, job, tech, _own_customer(session, admin.org_id, job.customer_id))
    return _outs(session, [job])[0]


@router.post("/{job_id}/start", response_model=JobOut)
def start_job(job_id: int, user: models.User = Depends(get_current_user), session: Session = Depends(get_session)):
    job = _visible_job(session, user, job_id)
    if job.status != "assigned":
        raise HTTPException(status_code=409, detail=f"A job that is '{job.status}' cannot be started")
    job.status = "in_progress"
    job.started_at = models.utcnow()
    session.add(job)
    session.commit()
    session.refresh(job)
    return _outs(session, [job])[0]


@router.post("/{job_id}/complete", response_model=JobOut)
def complete_job(job_id: int, user: models.User = Depends(get_current_user), session: Session = Depends(get_session)):
    job = _visible_job(session, user, job_id)
    if job.status not in ("assigned", "in_progress"):
        raise HTTPException(status_code=409, detail=f"A job that is '{job.status}' cannot be completed")
    now = models.utcnow()
    job.status = "done"
    job.started_at = job.started_at or now
    job.completed_at = now
    session.add(job)
    session.commit()
    session.refresh(job)
    return _outs(session, [job])[0]
