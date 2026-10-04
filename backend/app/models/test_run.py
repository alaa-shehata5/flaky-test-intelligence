"""CI test run model."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.test_execution import TestExecution


class TestRun(Base):
    __tablename__ = "test_runs"
    __table_args__ = (
        UniqueConstraint("project_id", "run_number", name="uq_test_runs_project_run"),
        Index("ix_test_runs_project_branch", "project_id", "branch"),
        Index("ix_test_runs_project_created", "project_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    run_number: Mapped[int] = mapped_column(Integer, nullable=False)
    commit_sha: Mapped[str | None] = mapped_column(String(64), nullable=True)
    branch: Mapped[str] = mapped_column(String(255), nullable=False, default="main")
    workflow_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    environment: Mapped[str | None] = mapped_column(String(255), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    total_tests: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    passed_tests: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_tests: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    skipped_tests: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_tests: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_duration: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    source: Mapped[str] = mapped_column(String(64), nullable=False, default="junit")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
        index=True,
    )

    project: Mapped[Project] = relationship("Project", back_populates="runs")
    executions: Mapped[list[TestExecution]] = relationship(
        "TestExecution", back_populates="run", cascade="all, delete-orphan"
    )
