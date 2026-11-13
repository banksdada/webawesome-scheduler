"""Database connection."""

import os

from sqlalchemy import inspect, text
from sqlmodel import Session, create_engine

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./scheduler.db")
# Coolify gives PostgreSQL addresses starting "postgres://" but SQLAlchemy needs "postgresql://"
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = "postgresql://" + DATABASE_URL[len("postgres://"):]

_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, echo=False, connect_args=_args)


def get_session():
    with Session(engine) as session:
        yield session


# Columns added after the first release. create_all() only makes missing TABLES, so existing
# databases need these added by hand. Each entry: (table, column, SQL type and default).
NEW_COLUMNS = [
    ("organisation", "sector", "VARCHAR NOT NULL DEFAULT 'cleaning'"),
    ("organisation", "suspended", "BOOLEAN NOT NULL DEFAULT FALSE"),
]


def upgrade_schema(eng=None) -> None:
    """Add any missing columns to tables that already exist. Safe to run on every start."""
    eng = eng or engine
    inspector = inspect(eng)
    for table, column, ddl in NEW_COLUMNS:
        if table in inspector.get_table_names() and column not in {c["name"] for c in inspector.get_columns(table)}:
            with eng.begin() as conn:
                conn.execute(text(f'ALTER TABLE "{table}" ADD COLUMN "{column}" {ddl}'))
