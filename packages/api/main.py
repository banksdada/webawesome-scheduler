"""FastAPI entry point for the Quick‑Stack experimental backend.

- Provides JWT‑based auth (simple token for demo).
- Uses SQLModel (SQLite for quick local testing; can be switched to Postgres via DATABASE_URL).
- Registers routers for customers and jobs (CRUD stubs).

*Environment variables (can be set via .env or system):
  DATABASE_URL               – SQLAlchemy connection (e.g. postgresql://... or sqlite:///./quickstack.db)
  SECRET_KEY                 – JWT signing key
  ALGORITHM                  – JWT algorithm (default HS256)
  ACCESS_TOKEN_EXPIRE_MINUTES – JWT token lifetime (minutes)
  NEXT_PUBLIC_API_URL         – used by the UI (optional)
  FEATURE_* environment variables can toggle optional modules (quotes, invoicing, etc.)
"""

import importlib
import logging
import os
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel import Session, SQLModel, create_engine, select
from datetime import datetime, timedelta
import jwt

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./quickstack.db")
# Coolify gives PostgreSQL addresses starting "postgres://" but SQLAlchemy needs "postgresql://"
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = "postgresql://" + DATABASE_URL[len("postgres://"):]
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Feature toggles (read from environment)
FEATURE_QUOTES = os.getenv("FEATURE_QUOTES", "1") == "1"
FEATURE_INVOICING = os.getenv("FEATURE_INVOICING", "0") == "1"  # not built yet
FEATURE_CALENDAR = os.getenv("FEATURE_CALENDAR", "0") == "1"  # not built yet
FEATURE_TEAM_MANAGEMENT = os.getenv("FEATURE_TEAM_MANAGEMENT", "0") == "1"  # not built yet
FEATURE_LIVE_UPDATES = os.getenv("FEATURE_LIVE_UPDATES", "0") == "1"  # not built yet

log = logging.getLogger("scheduler")

# Comma-separated list of website addresses allowed to call this API from a browser
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",") if o.strip()]

engine = create_engine(DATABASE_URL, echo=False)

# ---------------------------------------------------------------------------
# Models (imported lazily to avoid circular imports)
# ---------------------------------------------------------------------------
from . import models

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(title="WebAwesome Scheduler API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables on startup
@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)

# ---------------------------------------------------------------------------
# Auth utilities
# ---------------------------------------------------------------------------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub = payload.get("sub")
        if sub is None:
            raise credentials_exception
        user_id = int(sub)
    except (jwt.PyJWTError, ValueError):
        raise credentials_exception
    with Session(engine) as session:
        user = session.get(models.User, user_id)
        if user is None:
            raise credentials_exception
        return user

# ---------------------------------------------------------------------------
# Token endpoint (demo – password is plain text for simplicity)
# ---------------------------------------------------------------------------
@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # In a real app you would hash/verify the password.
    with Session(engine) as session:
        statement = select(models.User).where(models.User.email == form_data.username)
        user = session.exec(statement).first()
        if not user or form_data.password != "password":
            raise HTTPException(status_code=400, detail="Incorrect username or password")
        access_token = create_access_token(data={"sub": str(user.id)})  # PyJWT needs text here
        return {"access_token": access_token, "token_type": "bearer"}

# ---------------------------------------------------------------------------
# Health check for deployments (Coolify, Kubernetes probes)
# ---------------------------------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

# ---------------------------------------------------------------------------
# Include routers (CRUD for customers & jobs)
# ---------------------------------------------------------------------------
from .routers import customers, jobs

app.include_router(customers.router, prefix="/customers", tags=["customers"], dependencies=[Depends(get_current_user)])
app.include_router(jobs.router, prefix="/jobs", tags=["jobs"], dependencies=[Depends(get_current_user)])

# Optional modules. If a feature is switched on but its code does not exist yet,
# log a warning and carry on instead of crashing the whole API at start-up.
def include_optional(enabled: bool, module: str, prefix: str):
    if not enabled:
        return
    try:
        mod = importlib.import_module(f".routers.{module}", package=__package__)
    except ModuleNotFoundError as err:
        if err.name and err.name.endswith(f"routers.{module}"):
            log.warning("Feature '%s' is switched on but routers/%s.py does not exist yet - skipping", module, module)
            return
        raise  # a real error inside an existing module - do not hide it
    app.include_router(mod.router, prefix=prefix, tags=[module], dependencies=[Depends(get_current_user)])


include_optional(FEATURE_QUOTES, "quotes", "/quotes")
include_optional(FEATURE_INVOICING, "invoicing", "/invoices")
include_optional(FEATURE_CALENDAR, "calendar", "/calendar")
include_optional(FEATURE_TEAM_MANAGEMENT, "technicians", "/technicians")
include_optional(FEATURE_LIVE_UPDATES, "updates", "/updates")
