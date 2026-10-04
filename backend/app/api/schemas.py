"""API response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.analysis.classification import Classification


class ProjectCreate(BaseModel):
    name: str
    repository: str | None = None


class ProjectOut(BaseModel):
    id: int
    name: str
    repository: str | None
    created_at: datetime
    run_count: int = 0
    test_count: int = 0


class ProjectListOut(BaseModel):
    items: list[ProjectOut]
    total: int


class RunOut(BaseModel):
    id: int
    project_id: int
    project_name: str
    run_number: int
    branch: str
    commit_sha: str | None
    workflow_name: str | None
    environment: str | None
    started_at: datetime | None
    finished_at: datetime | None
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    error_tests: int
    total_duration: float
    source: str
    created_at: datetime


class RunListOut(BaseModel):
    items: list[RunOut]
    total: int
    limit: int
    offset: int


class TestListItem(BaseModel):
    test_case_id: int
    unique_key: str
    project_id: int
    project_name: str
    suite_name: str | None
    classname: str
    test_name: str
    classification: Classification
    flakiness_score: float
    pass_rate: float
    sample_size: int
    avg_duration: float
    last_seen_at: datetime
    newly_flaky: bool
    is_slow: bool


class TestListOut(BaseModel):
    items: list[TestListItem]
    total: int
    limit: int
    offset: int


class TestDetailOut(BaseModel):
    test_case_id: int
    unique_key: str
    project_id: int
    project_name: str
    suite_name: str | None
    classname: str
    test_name: str
    sample_size: int
    passed: int
    failed: int
    error: int
    skipped: int
    pass_rate: float
    failure_rate: float
    duration_min: float
    duration_max: float
    duration_mean: float
    duration_median: float
    duration_p95: float
    duration_stddev: float
    inconsistency: float
    recency: float
    duration_instability: float
    flakiness_score: float
    classification: Classification
    newly_flaky: bool
    persistently_flaky: bool
    is_slow: bool
    pass_rate_delta: float
    failure_rate_delta: float
    duration_delta: float
    score_delta: float


class HistoryPoint(BaseModel):
    run_id: int
    run_number: int
    branch: str
    status: str
    duration: float
    executed_at: datetime
    score: float
    failure_message: str | None
    failure_type: str | None


class FlakyListOut(BaseModel):
    items: list[TestListItem]
    total: int
    limit: int
    offset: int


class DashboardSummary(BaseModel):
    total_tests: int
    total_runs: int
    stable_tests: int
    suspected_flaky_tests: int
    highly_flaky_tests: int
    consistently_failing_tests: int
    slow_tests: int
    newly_flaky_tests: int
    average_pass_rate: float
