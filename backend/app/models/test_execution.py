"""Single test execution (one test in one run)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.test_case import TestCase
    from app.models.test_run import TestRun

VALID_STATUSES = ("passed", "failed", "error", "skipped")


class TestExecution(Base):
    __tablename__ = "test_executions"
    __table_args__ = (
        CheckConstraint(
            "status IN ('passed', 'failed', 'error', 'skipped')",
            name="ck_test_executions_status",
        ),
        Index("ix_test_executions_run_id", "run_id"),
        Index("ix_test_executions_test_case_id", "test_case_id"),
        Index("ix_test_executions_case_time", "test_case_id", "executed_at"),
        Index("ix_test_executions_executed_at", "executed_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(
        ForeignKey("test_runs.id", ondelete="CASCADE"), nullable=False
    )
    test_case_id: Mapped[int] = mapped_column(
        ForeignKey("test_cases.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    duration: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    failure_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    failure_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    executed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    run: Mapped[TestRun] = relationship("TestRun", back_populates="executions")
    test_case: Mapped[TestCase] = relationship("TestCase", back_populates="executions")
