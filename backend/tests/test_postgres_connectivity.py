"""Opt-in connectivity check for the Phase 1 PostgreSQL gate.

Set TEST_DATABASE_URL to a disposable PostgreSQL database to run this check.
SQLite model tests remain isolated and do not stand in for PostgreSQL coverage.
"""

import os

import pytest
from sqlalchemy import create_engine, text


def test_postgresql_accepts_a_connection():
    database_url = os.getenv("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("set TEST_DATABASE_URL to run the PostgreSQL connectivity gate")

    engine = create_engine(database_url, pool_pre_ping=True)
    try:
        assert engine.dialect.name == "postgresql"
        with engine.connect() as connection:
            assert connection.scalar(text("SELECT 1")) == 1
    finally:
        engine.dispose()
