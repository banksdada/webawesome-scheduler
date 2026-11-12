from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from .. import models
from ..db import get_session
from ..deps import require_admin
from ..schemas import CustomerIn, CustomerPatch

router = APIRouter(prefix="/customers", tags=["customers"])


def _get_own(session: Session, admin: models.User, customer_id: int) -> models.Customer:
    customer = session.get(models.Customer, customer_id)
    if not customer or customer.org_id != admin.org_id:
        raise HTTPException(status_code=404, detail="Not found")
    return customer


@router.post("", response_model=models.Customer)
def create_customer(body: CustomerIn, admin: models.User = Depends(require_admin), session: Session = Depends(get_session)):
    customer = models.Customer(org_id=admin.org_id, **body.model_dump())
    session.add(customer)
    session.commit()
    session.refresh(customer)
    return customer


@router.get("", response_model=list[models.Customer])
def list_customers(admin: models.User = Depends(require_admin), session: Session = Depends(get_session)):
    stmt = select(models.Customer).where(models.Customer.org_id == admin.org_id).order_by(models.Customer.name)
    return session.exec(stmt).all()


@router.get("/{customer_id}", response_model=models.Customer)
def get_customer(customer_id: int, admin: models.User = Depends(require_admin), session: Session = Depends(get_session)):
    return _get_own(session, admin, customer_id)


@router.patch("/{customer_id}", response_model=models.Customer)
def update_customer(
    customer_id: int, body: CustomerPatch, admin: models.User = Depends(require_admin), session: Session = Depends(get_session)
):
    customer = _get_own(session, admin, customer_id)
    for key, value in body.model_dump(exclude_unset=True).items():
        if key == "name" and value is None:
            continue  # name is required
        setattr(customer, key, value)
    session.add(customer)
    session.commit()
    session.refresh(customer)
    return customer
