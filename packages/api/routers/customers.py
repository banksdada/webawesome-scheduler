from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from .. import models
from ..main import engine, get_current_user

router = APIRouter()

# ---- CRUD – Customer ----
@router.post("")
def create_customer(customer: models.Customer, current_user: models.User = Depends(get_current_user)):
    if customer.owner_id is not None and customer.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot assign customer to another owner")
    customer.owner_id = current_user.id
    with Session(engine) as session:
        session.add(customer)
        session.commit()
        session.refresh(customer)
    return customer

@router.get("/{customer_id}")
def get_customer(customer_id: int, current_user: models.User = Depends(get_current_user)):
    with Session(engine) as session:
        customer = session.get(models.Customer, customer_id)
        if not customer or customer.owner_id != current_user.id:
            raise HTTPException(status_code=404, detail="Not found")
        return customer

# list – only customers belonging to the current user
@router.get("")
def list_customers(current_user: models.User = Depends(get_current_user)):
    with Session(engine) as session:
        stmt = select(models.Customer).where(models.Customer.owner_id == current_user.id)
        customers = session.exec(stmt).all()
    return customers