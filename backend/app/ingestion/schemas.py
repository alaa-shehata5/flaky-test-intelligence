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

    suite_name: str | None = Field(default=None, max_length=255)
    classname: str = Field(max_length=1024)
    test_name: str = Field(max_length=1024)
    status: TestStatus
    duration: float = Field(default=0.0, ge=0.0)
    failure_message: str | None = None
    failure_type: str | None = Field(default=None, max_length=255)


class TestRunResult(BaseModel):
    """One normalized CI run: metadata plus all case outcomes."""

    project: str = Field(min_length=1, max_length=255)
    run_number: int = Field(ge=1)
    branch: str = Field(default="main", max_length=255)
    commit_sha: str | None = Field(default=None, max_length=64)
    workflow_name: str | None = Field(default=None, max_length=255)
    environment: str | None = Field(default=None, max_length=255)
    cases: list[TestCaseResult] = Field(default_factory=list)
