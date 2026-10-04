"""Tests API: list with filters, detail, and execution history."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.analysis.service import analyze_test_case, run_ids_for_branch, test_history
from app.api.common import config_from_settings, scoped_cases, to_detail, to_list_item
from app.api.errors import ApiError
from app.api.schemas import HistoryPoint, TestDetailOut, TestListOut
from app.db.session import get_db
from app.models import Project, TestCase, TestRun

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
    suite: str | None = Query(None),
    classification: ClassificationFilter | None = Query(None),
    minimum_score: float | None = Query(None, ge=0.0, le=100.0),
    q: str | None = Query(None, description="Substring match on test/class name"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),  # noqa: B008
) -> TestListOut:
    config = config_from_settings()
    cases = scoped_cases(db, project_id)
    if suite is not None:
        cases = [c for c in cases if c.suite_name == suite]
    run_ids: list[int] | None = None
    if branch is not None:
        if project_id is not None:
            run_ids = run_ids_for_branch(db, project_id, branch)
        else:
            run_ids = list(db.scalars(select(TestRun.id).where(TestRun.branch == branch)))
    project_names = {p.id: p.name for p in db.scalars(select(Project)).all()}
    items = []
    for case in cases:
        analysis = analyze_test_case(db, case.id, config, run_ids)
        if classification is not None and analysis.classification != classification:
            continue
        if minimum_score is not None and analysis.flakiness_score < minimum_score:
            continue
        if q is not None and q.lower() not in (f"{case.classname} {case.test_name}".lower()):
            continue
        items.append(to_list_item(case, project_names[case.project_id], analysis))
    total = len(items)
    return TestListOut(
        items=items[offset : offset + limit], total=total, limit=limit, offset=offset
    )


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
