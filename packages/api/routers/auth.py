from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select

from .. import models
from ..db import get_session
from ..deps import get_current_user
from ..schemas import SignupIn, TokenOut, UserOut
from ..security import create_token, hash_password, verify_password

router = APIRouter(tags=["auth"])


def _find_user(session: Session, email: str):
    return session.exec(select(models.User).where(models.User.email == email.strip().lower())).first()


@router.post("/auth/signup", response_model=TokenOut)
def signup(body: SignupIn, session: Session = Depends(get_session)):
    """Create a new business account and its first admin."""
    if _find_user(session, body.email):
        raise HTTPException(status_code=409, detail="That email is already registered")
    org = models.Organisation(name=body.organisation_name.strip())
    session.add(org)
    session.commit()
    session.refresh(org)
    user = models.User(
        org_id=org.id,
        email=body.email.strip().lower(),
        name=body.name.strip(),
        role="admin",
        password_hash=hash_password(body.password),
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return TokenOut(access_token=create_token(user.id), role=user.role, name=user.name)


@router.post("/token", response_model=TokenOut)
def login(form: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    user = _find_user(session, form.username)
    if not user or not user.active or not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    return TokenOut(access_token=create_token(user.id), role=user.role, name=user.name)


@router.get("/me", response_model=UserOut)
def me(user: models.User = Depends(get_current_user)):
    return user
