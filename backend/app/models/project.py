"""Project model."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.test_case import TestCase
    from app.models.test_run import TestRun


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    repository: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    runs: Mapped[list[TestRun]] = relationship(
        "TestRun", back_populates="project", cascade="all, delete-orphan"
    )
    test_cases: Mapped[list[TestCase]] = relationship(
        "TestCase", back_populates="project", cascade="all, delete-orphan"
    )
