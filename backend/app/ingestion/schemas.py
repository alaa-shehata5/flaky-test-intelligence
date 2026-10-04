"""Normalized JUnit ingestion data model.

The secure XML parser produces these structures; the persistence service
stores them as projects / runs / test cases / executions.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

TestStatus = Literal["passed", "failed", "error", "skipped"]


class TestCaseResult(BaseModel):
    """One normalized test case outcome."""

    suite_name: str | None = None
    classname: str
    test_name: str
    status: TestStatus
    duration: float = Field(default=0.0, ge=0.0)
    failure_message: str | None = None
    failure_type: str | None = None


class TestRunResult(BaseModel):
    """One normalized CI run: metadata plus all case outcomes."""

    project: str = Field(min_length=1)
    run_number: int = Field(ge=1)
    branch: str = "main"
    commit_sha: str | None = None
    workflow_name: str | None = None
    environment: str | None = None
    cases: list[TestCaseResult] = Field(default_factory=list)
