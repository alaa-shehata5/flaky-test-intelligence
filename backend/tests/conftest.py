"""Shared pytest fixtures."""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

import app.models as models
from app.db.base import Base

# SQLAlchemy models share the Test* prefix; keep pytest from collecting them.
for _name in ("TestRun", "TestExecution", "TestCase"):
    getattr(models, _name).__test__ = False


@pytest.fixture()
def db_session() -> Session:
    """Isolated in-memory SQLite session with all tables created."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    session = factory()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()
