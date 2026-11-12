from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from .. import models
from ..db import get_session
from ..deps import require_admin
from ..schemas import TeamIn, TeamPatch, UserOut
from ..security import hash_password

router = APIRouter(prefix="/team", tags=["team"])


@router.get("", response_model=list[UserOut])
def list_team(admin: models.User = Depends(require_admin), session: Session = Depends(get_session)):
    return session.exec(select(models.User).where(models.User.org_id == admin.org_id).order_by(models.User.name)).all()


@router.post("", response_model=UserOut)
def add_member(body: TeamIn, admin: models.User = Depends(require_admin), session: Session = Depends(get_session)):
    email = body.email.strip().lower()
    if session.exec(select(models.User).where(models.User.email == email)).first():
        raise HTTPException(status_code=409, detail="That email is already registered")
    user = models.User(
        org_id=admin.org_id,
        email=email,
        name=body.name.strip(),
        phone=body.phone,
        role=body.role,
        password_hash=hash_password(body.password),
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@router.patch("/{user_id}", response_model=UserOut)
def update_member(
    user_id: int, body: TeamPatch, admin: models.User = Depends(require_admin), session: Session = Depends(get_session)
):
    user = session.get(models.User, user_id)
    if not user or user.org_id != admin.org_id:
        raise HTTPException(status_code=404, detail="Not found")
    if user.id == admin.id and body.active is False:
        raise HTTPException(status_code=409, detail="You cannot deactivate yourself")
    for key, value in body.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(user, key, value)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user
