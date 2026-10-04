"""Engine + session management."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

_engine = None
_SessionLocal: sessionmaker[Session] | None = None


def get_engine():
    """Return a process-wide engine built from current settings."""
    global _engine, _SessionLocal
    if _engine is None:
        settings = get_settings()
        connect_args = {}
        # SQLite needs explicit thread handling for tests/local fallback.
        if settings.database_url.startswith("sqlite"):
            connect_args = {"check_same_thread": False}
        _engine = create_engine(
            settings.database_url, pool_pre_ping=True, connect_args=connect_args
        )
        _SessionLocal = sessionmaker(bind=_engine, autoflush=False, expire_on_commit=False)
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    get_engine()
    assert _SessionLocal is not None
    return _SessionLocal


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a request-scoped session."""
    factory = get_session_factory()
    db = factory()
    try:
        yield db
    finally:
        db.close()


def reset_engine() -> None:
    """Test helper: drop cached engine so new settings take effect."""
    global _engine, _SessionLocal
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _SessionLocal = None
