"""Dashboard API: system-health summary."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.analysis.service import analyze_test_case, run_ids_for_branch
from app.api.common import config_from_settings, get_project_or_404
from app.api.schemas import DashboardSummary
from app.db.session import get_db
from app.models import TestCase, TestRun

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def dashboard_summary(
    project_id: int | None = Query(None),
    branch: str | None = Query(None),
    db: Session = Depends(get_db),  # noqa: B008
) -> DashboardSummary:
    config = config_from_settings()
    if project_id is not None:
        get_project_or_404(db, project_id)

    run_q = select(func.count()).select_from(TestRun)
    if project_id is not None:
        run_q = run_q.where(TestRun.project_id == project_id)
    if branch is not None:
        run_q = run_q.where(TestRun.branch == branch)
    total_runs = db.scalar(run_q) or 0

    case_q = select(TestCase).order_by(TestCase.id)
    if project_id is not None:
        case_q = case_q.where(TestCase.project_id == project_id)
    cases = list(db.scalars(case_q))

    run_ids: list[int] | None = None
    if branch is not None:
        if project_id is not None:
            run_ids = run_ids_for_branch(db, project_id, branch)
        else:
            run_ids = list(db.scalars(select(TestRun.id).where(TestRun.branch == branch)))

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
        analysis = analyze_test_case(db, case.id, config, run_ids)
        if branch is not None and analysis.sample_size == 0:
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
