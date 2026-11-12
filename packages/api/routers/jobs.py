from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from .. import models
from ..main import engine, get_current_user

router = APIRouter()

# ---- CRUD – Job ----
@router.post("")
def create_job(job: models.Job, current_user: models.User = Depends(get_current_user)):
    # Ensure the customer belongs to current user
    with Session(engine) as session:
        customer = session.get(models.Customer, job.customer_id)
        if not customer or customer.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Cannot create job for another user’s customer")
        session.add(job)
        session.commit()
        session.refresh(job)
    return job

@router.get("/{job_id}")
def get_job(job_id: int, current_user: models.User = Depends(get_current_user)):
    with Session(engine) as session:
        job = session.get(models.Job, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Not found")
        # authorization: job.customer.owner_id must match current_user.id
        customer = session.get(models.Customer, job.customer_id)
        if customer.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")
        return job

@router.get("")
def list_jobs(current_user: models.User = Depends(get_current_user)):
    with Session(engine) as session:
        stmt = (
            select(models.Job)
            .join(models.Customer)
            .where(models.Customer.owner_id == current_user.id)
        )
        jobs = session.exec(stmt).all()
    return jobs