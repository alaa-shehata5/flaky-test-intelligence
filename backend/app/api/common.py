"""Shared helpers for API routers."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.analysis.service import AnalysisConfig, TestAnalysis
from app.api.errors import ApiError
from app.api.schemas import TestDetailOut, TestListItem
from app.core.config import get_settings
from app.models import Project, TestCase


def config_from_settings() -> AnalysisConfig:
    return AnalysisConfig.from_settings(get_settings())


def get_project_or_404(session: Session, project_id: int) -> Project:
    project = session.get(Project, project_id)
    if project is None:
        raise ApiError("PROJECT_NOT_FOUND", f"project {project_id} not found", 404)
    return project


def scoped_cases(session: Session, project_id: int | None) -> list[TestCase]:
    if project_id is not None:
        get_project_or_404(session, project_id)
        return list(
            session.scalars(
                select(TestCase).where(TestCase.project_id == project_id).order_by(TestCase.id)
            )
        )
    return list(session.scalars(select(TestCase).order_by(TestCase.id)))


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
        sample_size=analysis.sample_size,
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
