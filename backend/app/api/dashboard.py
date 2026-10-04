"""Dashboard API: system-health summary."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.analysis.service import analyze_test_case
from app.api.common import (
    config_from_settings,
    get_project_or_404,
    restrict_cases_to_runs,
    run_scope_query,
)
from app.api.schemas import DashboardSummary
from app.api.tests import ClassificationFilter
from app.db.session import get_db
from app.models import TestCase, TestRun

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def dashboard_summary(
    project_id: int | None = Query(None),
    branch: str | None = Query(None),
    workflow_name: str | None = Query(None),
    environment: str | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    classification: ClassificationFilter | None = Query(None),
    minimum_score: float | None = Query(None, ge=0.0, le=100.0),
    db: Session = Depends(get_db),  # noqa: B008
) -> DashboardSummary:
    config = config_from_settings()
    if project_id is not None:
        get_project_or_404(db, project_id)

    run_ids = run_scope_query(
        project_id=project_id,
        branch=branch,
        workflow_name=workflow_name,
        environment=environment,
        date_from=date_from,
        date_to=date_to,
    )
    run_q = select(func.count()).select_from(TestRun).where(TestRun.id.in_(run_ids))
    total_runs = db.scalar(run_q) or 0

    case_q = select(TestCase).order_by(TestCase.id)
    if project_id is not None:
        case_q = case_q.where(TestCase.project_id == project_id)
    has_run_filter = any((branch, workflow_name, environment, date_from, date_to))
    scoped_run_ids = run_ids if has_run_filter else None
    if has_run_filter:
        case_q = restrict_cases_to_runs(case_q, run_ids)
    cases = list(db.scalars(case_q))

    counts = {
        "STABLE": 0,
        "MOSTLY_STABLE": 0,
        "SUSPECTED_FLAKY": 0,
        "HIGHLY_FLAKY": 0,
        "CONSISTENTLY_FAILING": 0,
        "INSUFFICIENT_DATA": 0,
    }
    slow = newly = 0
    pass_rates: list[float] = []
    visible = 0
    for case in cases:
        analysis = analyze_test_case(db, case.id, config, scoped_run_ids)
        if has_run_filter and analysis.sample_size == 0:
            continue
        if classification is not None and analysis.classification != classification:
            continue
        if minimum_score is not None and analysis.flakiness_score < minimum_score:
            continue
        visible += 1
        counts[analysis.classification] += 1
        slow += 1 if analysis.is_slow else 0
        newly += 1 if analysis.newly_flaky else 0
        if analysis.sample_size > 0:
            pass_rates.append(analysis.pass_rate)

    return DashboardSummary(
        total_tests=visible,
        total_runs=total_runs,
        stable_tests=counts["STABLE"],
        suspected_flaky_tests=counts["SUSPECTED_FLAKY"],
        highly_flaky_tests=counts["HIGHLY_FLAKY"],
        consistently_failing_tests=counts["CONSISTENTLY_FAILING"],
        slow_tests=slow,
        newly_flaky_tests=newly,
        average_pass_rate=(sum(pass_rates) / len(pass_rates)) if pass_rates else 0.0,
    )
