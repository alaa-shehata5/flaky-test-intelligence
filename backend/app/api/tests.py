"""Tests API: list with filters, detail, and execution history."""

from __future__ import annotations

from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.analysis.service import analyze_test_case, test_history
from app.api.common import (
    config_from_settings,
    restrict_cases_to_runs,
    run_scope_query,
    scoped_case_query,
    to_detail,
    to_list_item,
)
from app.api.errors import ApiError
from app.api.schemas import HistoryPoint, TestDetailOut, TestListOut
from app.db.session import get_db
from app.models import Project, TestCase

router = APIRouter(prefix="/api/tests", tags=["tests"])

ClassificationFilter = Literal[
    "INSUFFICIENT_DATA",
    "STABLE",
    "MOSTLY_STABLE",
    "SUSPECTED_FLAKY",
    "HIGHLY_FLAKY",
    "CONSISTENTLY_FAILING",
]


@router.get("", response_model=TestListOut)
def list_tests(
    project_id: int | None = Query(None),
    branch: str | None = Query(None),
    workflow_name: str | None = Query(None),
    environment: str | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    suite: str | None = Query(None),
    classification: ClassificationFilter | None = Query(None),
    minimum_score: float | None = Query(None, ge=0.0, le=100.0),
    q: str | None = Query(None, description="Substring match on test/class name"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),  # noqa: B008
) -> TestListOut:
    config = config_from_settings()
    query = scoped_case_query(db, project_id)
    if suite is not None:
        query = query.where(TestCase.suite_name == suite)
    if q is not None:
        query = query.where(
            or_(TestCase.classname.ilike(f"%{q}%"), TestCase.test_name.ilike(f"%{q}%"))
        )
    run_ids = run_scope_query(
        project_id=project_id,
        branch=branch,
        workflow_name=workflow_name,
        environment=environment,
        date_from=date_from,
        date_to=date_to,
    )
    if any((branch, workflow_name, environment, date_from, date_to)):
        query = restrict_cases_to_runs(query, run_ids)
    else:
        run_ids = None
    project_names = {p.id: p.name for p in db.scalars(select(Project)).all()}

    # Classification and score are computed values, so filtered requests must
    # inspect candidates before they can page. Keep only the requested slice in
    # memory. When those filters are absent, use native database count/pagination.
    if classification is None and minimum_score is None:
        count_query = select(func.count()).select_from(query.order_by(None).subquery())
        total = db.scalar(count_query) or 0
        page_cases = db.scalars(query.limit(limit).offset(offset)).all()
        items = [
            to_list_item(
                case,
                project_names[case.project_id],
                analyze_test_case(db, case.id, config, run_ids),
            )
            for case in page_cases
        ]
        return TestListOut(items=items, total=total, limit=limit, offset=offset)

    items = []
    total = 0
    for case in db.scalars(query.execution_options(yield_per=100)):
        analysis = analyze_test_case(db, case.id, config, run_ids)
        if classification is not None and analysis.classification != classification:
            continue
        if minimum_score is not None and analysis.flakiness_score < minimum_score:
            continue
        total += 1
        if offset <= total - 1 < offset + limit:
            items.append(to_list_item(case, project_names[case.project_id], analysis))
    return TestListOut(items=items, total=total, limit=limit, offset=offset)


@router.get("/{test_id}", response_model=TestDetailOut)
def get_test(test_id: int, db: Session = Depends(get_db)) -> TestDetailOut:  # noqa: B008
    case = db.get(TestCase, test_id)
    if case is None:
        raise ApiError("TEST_NOT_FOUND", f"test {test_id} not found", 404)
    project = db.get(Project, case.project_id)
    analysis = analyze_test_case(db, case.id, config_from_settings())
    return to_detail(case, project.name if project else "?", analysis)


@router.get("/{test_id}/history", response_model=list[HistoryPoint])
def get_test_history(test_id: int, db: Session = Depends(get_db)) -> list[HistoryPoint]:  # noqa: B008
    try:
        points = test_history(db, test_id, config_from_settings())
    except ValueError as exc:
        raise ApiError("TEST_NOT_FOUND", str(exc), 404) from exc
    return [
        HistoryPoint(
            run_id=p.run_id,
            run_number=p.run_number,
            branch=p.branch,
            status=p.status,
            duration=p.duration,
            executed_at=p.executed_at,
            score=p.score,
            failure_message=p.failure_message,
            failure_type=p.failure_type,
        )
        for p in points
    ]
