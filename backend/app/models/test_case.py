"""Logical test case model with deterministic identity."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.test_execution import TestExecution


class TestCase(Base):
    __tablename__ = "test_cases"
    __table_args__ = (
        Index("ix_test_cases_project_class_name", "project_id", "classname", "test_name"),
        Index("ix_test_cases_last_seen", "last_seen_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    suite_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    classname: Mapped[str] = mapped_column(String(1024), nullable=False)
    test_name: Mapped[str] = mapped_column(String(1024), nullable=False)
    # Logical identity: "project::classname::test_name" (project resolved by name).
    unique_key: Mapped[str] = mapped_column(String(2048), unique=True, nullable=False, index=True)
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    project: Mapped[Project] = relationship("Project", back_populates="test_cases")
    executions: Mapped[list[TestExecution]] = relationship(
        "TestExecution", back_populates="test_case", cascade="all, delete-orphan"
    )
