import hashlib
import os
import secrets
from datetime import timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select

from .. import models, notify
from ..db import get_session
from ..deps import SUSPENDED_MESSAGE, get_current_user, is_platform_admin
from ..schemas import ForgotIn, ResetIn, SignupIn, TokenOut, UserOut
from ..security import create_token, hash_password, verify_password

router = APIRouter(tags=["auth"])

RESET_MINUTES = 60  # how long a reset link works
MAX_RESETS_PER_HOUR = 3  # per account, so nobody can flood an inbox


def _fingerprint(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


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
    return TokenOut(access_token=create_token(user.id), role=user.role, name=user.name, platform_admin=is_platform_admin(user))


@router.post("/token", response_model=TokenOut)
def login(form: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    user = _find_user(session, form.username)
    if not user or not user.active or not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    org = session.get(models.Organisation, user.org_id)
    if org is not None and org.suspended and not is_platform_admin(user):
        raise HTTPException(status_code=403, detail=SUSPENDED_MESSAGE)
    return TokenOut(access_token=create_token(user.id), role=user.role, name=user.name, platform_admin=is_platform_admin(user))


@router.post("/auth/forgot")
def forgot_password(body: ForgotIn, background: BackgroundTasks, session: Session = Depends(get_session)):
    """Email a reset link. The answer is always the same, so nobody can use this to find out who has an account."""
    user = _find_user(session, body.email)
    if user and user.active:
        org = session.get(models.Organisation, user.org_id)
        suspended = bool(org and org.suspended and not is_platform_admin(user))
        since = models.utcnow() - timedelta(hours=1)
        recent = session.exec(
            select(models.PasswordReset).where(models.PasswordReset.user_id == user.id, models.PasswordReset.created_at > since)
        ).all()
        if not suspended and len(recent) < MAX_RESETS_PER_HOUR:
            secret = secrets.token_urlsafe(32)
            expires = models.utcnow() + timedelta(minutes=RESET_MINUTES)
            session.add(models.PasswordReset(user_id=user.id, token_hash=_fingerprint(secret), expires_at=expires))
            session.commit()
            site = os.getenv("SITE_URL", "").rstrip("/")
            background.add_task(notify.password_reset, user.email, user.name, f"{site}/reset?token={secret}")
    return {"ok": True}


@router.post("/auth/reset")
def reset_password(body: ResetIn, session: Session = Depends(get_session)):
    """Set a new password using the link from the email. Each link works once."""
    record = session.exec(select(models.PasswordReset).where(models.PasswordReset.token_hash == _fingerprint(body.token))).first()
    if not record or record.used or record.expires_at < models.utcnow():
        raise HTTPException(status_code=400, detail="This link has expired or has already been used. Ask for a new one.")
    user = session.get(models.User, record.user_id)
    if not user or not user.active:
        raise HTTPException(status_code=400, detail="This link has expired or has already been used. Ask for a new one.")
    user.password_hash = hash_password(body.password)
    session.add(user)
    # Retire every link for this person, not just the one used.
    for other in session.exec(select(models.PasswordReset).where(models.PasswordReset.user_id == user.id)).all():
        other.used = True
        session.add(other)
    session.commit()
    return {"ok": True}


@router.get("/me", response_model=UserOut)
def me(user: models.User = Depends(get_current_user)):
    return UserOut(
        id=user.id, name=user.name, email=user.email, phone=user.phone, role=user.role, active=user.active,
        platform_admin=is_platform_admin(user),
    )
