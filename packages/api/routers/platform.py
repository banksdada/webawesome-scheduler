"""Owner-only screens: see every business that uses the tool, suspend or reactivate one."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlmodel import Session, select

from .. import models
from ..db import get_session
from ..deps import require_platform_admin
from ..schemas import OrgSummary

router = APIRouter(prefix="/platform", tags=["platform"])


def _counts(session: Session, table, org_ids) -> dict:
    rows = session.exec(select(table.org_id, func.count()).where(table.org_id.in_(org_ids)).group_by(table.org_id)).all()
    return {org_id: n for org_id, n in rows}


@router.get("/orgs", response_model=list[OrgSummary])
def list_orgs(admin: models.User = Depends(require_platform_admin), session: Session = Depends(get_session)):
    orgs = session.exec(select(models.Organisation).order_by(models.Organisation.id.desc())).all()
    ids = [o.id for o in orgs]
    users, customers, jobs = (_counts(session, t, ids) for t in (models.User, models.Customer, models.Job))
    return [
        OrgSummary(
            id=o.id, name=o.name, sector=o.sector, suspended=o.suspended, created_at=o.created_at,
            users=users.get(o.id, 0), customers=customers.get(o.id, 0), jobs=jobs.get(o.id, 0),
        )
        for o in orgs
    ]


def _set_suspended(org_id: int, value: bool, admin: models.User, session: Session) -> OrgSummary:
    org = session.get(models.Organisation, org_id)
    if org is None:
        raise HTTPException(status_code=404, detail="Business not found")
    if value and org.id == admin.org_id:
        raise HTTPException(status_code=400, detail="You can't suspend your own business")
    org.suspended = value
    session.add(org)
    session.commit()
    session.refresh(org)
    return next(o for o in list_orgs(admin, session) if o.id == org.id)


@router.post("/orgs/{org_id}/suspend", response_model=OrgSummary)
def suspend(org_id: int, admin: models.User = Depends(require_platform_admin), session: Session = Depends(get_session)):
    return _set_suspended(org_id, True, admin, session)


@router.post("/orgs/{org_id}/reactivate", response_model=OrgSummary)
def reactivate(org_id: int, admin: models.User = Depends(require_platform_admin), session: Session = Depends(get_session)):
    return _set_suspended(org_id, False, admin, session)
