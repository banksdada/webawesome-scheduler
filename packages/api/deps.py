"""Shared checks used by the routers: who is logged in, and are they an admin."""

import os

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session

from . import models
from .db import get_session
from .security import read_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")


def platform_admin_emails() -> set[str]:
    """Owner email addresses, from the PLATFORM_ADMIN_EMAILS setting (comma separated)."""
    return {e.strip().lower() for e in os.getenv("PLATFORM_ADMIN_EMAILS", "").split(",") if e.strip()}


def is_platform_admin(user: models.User) -> bool:
    return user.active and user.email.lower() in platform_admin_emails()


SUSPENDED_MESSAGE = "This account is suspended. Please contact support."


def get_current_user(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)) -> models.User:
    user_id = read_token(token)
    user = session.get(models.User, user_id) if user_id is not None else None
    if user is None or not user.active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    org = session.get(models.Organisation, user.org_id)
    if org is not None and org.suspended and not is_platform_admin(user):
        raise HTTPException(status_code=403, detail=SUSPENDED_MESSAGE)
    return user


def require_platform_admin(user: models.User = Depends(get_current_user)) -> models.User:
    if not is_platform_admin(user):
        raise HTTPException(status_code=403, detail="Platform admins only")
    return user


def require_admin(user: models.User = Depends(get_current_user)) -> models.User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admins only")
    return user
