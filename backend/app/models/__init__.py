"""Model registry. Import all models here so Alembic autogenerate sees them."""

from app.db.base import Base
from app.models.project import Project
from app.models.test_case import TestCase
from app.models.test_execution import TestExecution
from app.models.test_run import TestRun

__all__ = ["Base", "Project", "TestCase", "TestExecution", "TestRun"]
