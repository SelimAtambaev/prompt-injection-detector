"""Engine and session management.

DB-agnostic: the URL comes from config (SQLite by default, Postgres in prod).
The default session factory is created lazily and cached. Tests build their own
factory against a throwaway database via ``make_session_factory`` so they never
touch the app's real database.
"""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.storage.models import Base

_default_factory: sessionmaker[Session] | None = None


def make_session_factory(url: str) -> sessionmaker[Session]:
    engine = create_engine(url, future=True)
    Base.metadata.create_all(engine)  # idempotent: creates tables if absent
    return sessionmaker(bind=engine, future=True)


def default_session_factory() -> sessionmaker[Session]:
    global _default_factory
    if _default_factory is None:
        _default_factory = make_session_factory(settings.database_url)
    return _default_factory
