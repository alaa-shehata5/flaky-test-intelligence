"""Flaky-tests API: ranked view of tests worth investigating."""

from __future__ import annotations

import heapq
from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.analysis.classification import FLAKY_CLASSIFICATIONS
from app.analysis.service import analyze_test_case
from app.api.common import (
    config_from_settings,
    restrict_cases_to_runs,
    run_scope_query,
    scoped_case_query,
    to_list_item,
)
from app.api.schemas import FlakyListOut
from app.api.tests import ClassificationFilter
from app.db.session import get_db
from app.models import Project, TestCase

router = APIRouter(prefix="/api/flaky-tests", tags=["flaky-tests"])

SortKey = Literal["score_desc", "score_asc", "pass_rate_asc", "pass_rate_desc", "name_asc"]


@router.get("", response_model=FlakyListOut)
def list_flaky_tests(
    project_id: int | None = Query(None),
    branch: str | None = Query(None),
    workflow_name: str | None = Query(None),
    environment: str | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    classification: ClassificationFilter | None = Query(None),
    minimum_score: float | None = Query(None, ge=0.0, le=100.0),
    q: str | None = Query(None, description="Substring match on test/class name"),
    sort: SortKey = Query("score_desc"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),  # noqa: B008
) -> FlakyListOut:
    config = config_from_settings()
    threshold = config.flaky_threshold if minimum_score is None else minimum_score
    query = scoped_case_query(db, project_id)
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
    if q is not None:
        query = query.where(TestCase.classname.ilike(f"%{q}%") | TestCase.test_name.ilike(f"%{q}%"))
    project_names = {p.id: p.name for p in db.scalars(select(Project)).all()}

    matched = 0

    def analyzed_items():
        nonlocal matched
        for case in db.scalars(query.execution_options(yield_per=100)):
            analysis = analyze_test_case(db, case.id, config, run_ids)
            is_flaky = analysis.classification in FLAKY_CLASSIFICATIONS
            # Newly-flaky tests bypass the score gate (same rule as flakyctl).
            if not (analysis.newly_flaky or (is_flaky and analysis.flakiness_score >= threshold)):
                continue
            if classification is not None and analysis.classification != classification:
                continue
            matched += 1
            yield to_list_item(case, project_names[case.project_id], analysis)

    key_functions = {
        "score_desc": lambda item: item.flakiness_score,
        "score_asc": lambda item: item.flakiness_score,
        "pass_rate_asc": lambda item: item.pass_rate,
        "pass_rate_desc": lambda item: item.pass_rate,
        "name_asc": lambda item: item.unique_key,
    }
    n = offset + limit
    if sort in ("score_desc", "pass_rate_desc"):
        top = heapq.nlargest(n, analyzed_items(), key=key_functions[sort])
    else:
        top = heapq.nsmallest(n, analyzed_items(), key=key_functions[sort])
    items = top[offset : offset + limit]
    return FlakyListOut(items=items, total=matched, limit=limit, offset=offset)
