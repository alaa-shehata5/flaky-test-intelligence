"""Flaky-tests API: ranked view of tests worth investigating."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.analysis.classification import FLAKY_CLASSIFICATIONS
from app.analysis.service import analyze_test_case, run_ids_for_branch
from app.api.common import config_from_settings, scoped_cases, to_list_item
from app.api.schemas import FlakyListOut
from app.api.tests import ClassificationFilter
from app.db.session import get_db
from app.models import Project, TestRun

router = APIRouter(prefix="/api/flaky-tests", tags=["flaky-tests"])

SortKey = Literal["score_desc", "score_asc", "pass_rate_asc", "pass_rate_desc", "name_asc"]


@router.get("", response_model=FlakyListOut)
def list_flaky_tests(
    project_id: int | None = Query(None),
    branch: str | None = Query(None),
    classification: ClassificationFilter | None = Query(None),
    minimum_score: float | None = Query(None, ge=0.0, le=100.0),
    sort: SortKey = Query("score_desc"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),  # noqa: B008
) -> FlakyListOut:
    config = config_from_settings()
    threshold = config.flaky_threshold if minimum_score is None else minimum_score
    cases = scoped_cases(db, project_id)
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
        is_flaky = analysis.classification in FLAKY_CLASSIFICATIONS
        # Newly-flaky tests bypass the score gate (same rule as flakyctl).
        if not (analysis.newly_flaky or (is_flaky and analysis.flakiness_score >= threshold)):
            continue
        if classification is not None and analysis.classification != classification:
            continue
        items.append(to_list_item(case, project_names[case.project_id], analysis))
    if sort == "score_desc":
        items.sort(key=lambda i: i.flakiness_score, reverse=True)
    elif sort == "score_asc":
        items.sort(key=lambda i: i.flakiness_score)
    elif sort == "pass_rate_asc":
        items.sort(key=lambda i: i.pass_rate)
    elif sort == "pass_rate_desc":
        items.sort(key=lambda i: i.pass_rate, reverse=True)
    else:
        items.sort(key=lambda i: i.unique_key)
    total = len(items)
    return FlakyListOut(
        items=items[offset : offset + limit], total=total, limit=limit, offset=offset
    )
