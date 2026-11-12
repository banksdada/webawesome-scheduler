"""WebAwesome Scheduler API - job scheduling and dispatch.

Settings come from environment variables (see .env.template in the project root).
"""

import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel

from . import models  # noqa: F401  (makes sure the tables are known)
from .db import engine
from .routers import auth, customers, jobs, quotes, team

# Website address(es) allowed to call this API from a browser, comma separated
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",") if o.strip()]


@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine)  # creates missing tables on start-up
    yield


app = FastAPI(title="WebAwesome Scheduler API", version="0.2.0", lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS, allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


app.include_router(auth.router)
app.include_router(team.router)
app.include_router(customers.router)
app.include_router(jobs.router)
app.include_router(quotes.router)
