"""Shared helpers for API routers."""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.analysis.service import AnalysisConfig, TestAnalysis
from app.api.errors import ApiError
from app.api.schemas import TestDetailOut, TestListItem
from app.core.config import get_settings
from app.models import Project, TestCase, TestExecution, TestRun


def config_from_settings() -> AnalysisConfig:
    return AnalysisConfig.from_settings(get_settings())


def get_project_or_404(session: Session, project_id: int) -> Project:
    project = session.get(Project, project_id)
    if project is None:
        raise ApiError("PROJECT_NOT_FOUND", f"project {project_id} not found", 404)
    return project


def scoped_case_query(session: Session, project_id: int | None) -> Select[tuple[TestCase]]:
    if project_id is not None:
        get_project_or_404(session, project_id)
        return select(TestCase).where(TestCase.project_id == project_id).order_by(TestCase.id)
    return select(TestCase).order_by(TestCase.id)


def run_scope_query(
    *,
    project_id: int | None = None,
    branch: str | None = None,
    workflow_name: str | None = None,
    environment: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> Select[tuple[int]]:
    """Build a composable run-ID filter shared by dashboard-facing endpoints."""
    query = select(TestRun.id)
    if project_id is not None:
        query = query.where(TestRun.project_id == project_id)
    if branch is not None:
        query = query.where(TestRun.branch == branch)
    if workflow_name is not None:
        query = query.where(TestRun.workflow_name == workflow_name)
    if environment is not None:
        query = query.where(TestRun.environment == environment)
    if date_from is not None:
        query = query.where(TestRun.started_at >= datetime.combine(date_from, time.min, tzinfo=UTC))
    if date_to is not None:
        query = query.where(
            TestRun.started_at < datetime.combine(date_to + timedelta(days=1), time.min, tzinfo=UTC)
        )
    return query


def restrict_cases_to_runs(
    query: Select[tuple[TestCase]], run_ids: Select[tuple[int]]
) -> Select[tuple[TestCase]]:
    """Limit logical tests to those with an execution in the selected runs."""
    case_ids = select(TestExecution.test_case_id).where(TestExecution.run_id.in_(run_ids))
    return query.where(TestCase.id.in_(case_ids))


def to_list_item(test_case: TestCase, project_name: str, analysis: TestAnalysis) -> TestListItem:
    return TestListItem(
        test_case_id=test_case.id,
        unique_key=test_case.unique_key,
        project_id=test_case.project_id,
        project_name=project_name,
        suite_name=test_case.suite_name,
        classname=test_case.classname,
        test_name=test_case.test_name,
        classification=analysis.classification,
        flakiness_score=analysis.flakiness_score,
        pass_rate=analysis.pass_rate,
        failure_rate=analysis.failure_rate,
        sample_size=analysis.sample_size,
        pass_rate_delta=analysis.pass_rate_delta,
        score_delta=analysis.score_delta,
        avg_duration=analysis.duration_mean,
        last_seen_at=test_case.last_seen_at,
        newly_flaky=analysis.newly_flaky,
        is_slow=analysis.is_slow,
    )


def to_detail(test_case: TestCase, project_name: str, analysis: TestAnalysis) -> TestDetailOut:
    return TestDetailOut(
        test_case_id=test_case.id,
        unique_key=test_case.unique_key,
        project_id=test_case.project_id,
        project_name=project_name,
        suite_name=test_case.suite_name,
        classname=test_case.classname,
        test_name=test_case.test_name,
        **analysis.model_dump(exclude={"test_case_id", "unique_key"}),
    )
