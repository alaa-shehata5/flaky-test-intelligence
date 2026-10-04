"""Runs API: list, detail, and JUnit upload."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.common import get_project_or_404, run_scope_query
from app.api.errors import ApiError
from app.api.schemas import RunListOut, RunOut
from app.db.session import get_db
from app.ingestion.parser import MAX_JUNIT_BYTES, JUnitParseError, parse_junit
from app.ingestion.schemas import TestRunResult
from app.ingestion.service import (
    ConflictingDuplicateTestError,
    DuplicateRunError,
    persist_run,
)
from app.models import Project, TestRun

router = APIRouter(prefix="/api/runs", tags=["runs"])


def _to_out(run: TestRun, project_name: str) -> RunOut:
    return RunOut(
        id=run.id,
        project_id=run.project_id,
        project_name=project_name,
        run_number=run.run_number,
        branch=run.branch,
        commit_sha=run.commit_sha,
        workflow_name=run.workflow_name,
        environment=run.environment,
        started_at=run.started_at,
        finished_at=run.finished_at,
        total_tests=run.total_tests,
        passed_tests=run.passed_tests,
        failed_tests=run.failed_tests,
        skipped_tests=run.skipped_tests,
        error_tests=run.error_tests,
        total_duration=run.total_duration,
        source=run.source,
        created_at=run.created_at,
    )


@router.get("", response_model=RunListOut)
def list_runs(
    project_id: int | None = Query(None),
    branch: str | None = Query(None),
    workflow_name: str | None = Query(None),
    environment: str | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),  # noqa: B008
) -> RunListOut:
    query = select(TestRun, Project.name).join(Project, Project.id == TestRun.project_id)
    run_ids = run_scope_query(
        project_id=project_id,
        branch=branch,
        workflow_name=workflow_name,
        environment=environment,
        date_from=date_from,
        date_to=date_to,
    )
    query = query.where(TestRun.id.in_(run_ids))
    count_q = select(func.count()).select_from(TestRun).where(TestRun.id.in_(run_ids))
    if project_id is not None:
        get_project_or_404(db, project_id)
    total = db.scalar(count_q) or 0
    rows = db.execute(query.order_by(TestRun.id.desc()).limit(limit).offset(offset)).all()
    return RunListOut(
        items=[_to_out(run, name) for run, name in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{run_id}", response_model=RunOut)
def get_run(run_id: int, db: Session = Depends(get_db)) -> RunOut:  # noqa: B008
    row = db.execute(
        select(TestRun, Project.name)
        .join(Project, Project.id == TestRun.project_id)
        .where(TestRun.id == run_id)
    ).first()
    if row is None:
        raise ApiError("RUN_NOT_FOUND", f"run {run_id} not found", 404)
    run, name = row
    return _to_out(run, name)


@router.post("/upload", status_code=201)
def upload_run(
    file: UploadFile = File(...),
    project: str = Form(...),
    run_number: int = Form(...),
    branch: str = Form("main"),
    commit_sha: str | None = Form(None),
    workflow_name: str | None = Form(None),
    environment: str | None = Form(None),
    db: Session = Depends(get_db),
) -> dict:
    filename = (file.filename or "").lower()
    if not filename.endswith(".xml"):
        raise ApiError(
            "INVALID_FILE_TYPE",
            "Only JUnit XML files (.xml) are accepted.",
            status_code=400,
        )
    # Read at most one byte beyond the accepted size. Calling read() without a
    # bound allows an oversized multipart upload to consume arbitrary memory
    # before it is rejected.
    raw = file.file.read(MAX_JUNIT_BYTES + 1)
    if len(raw) > MAX_JUNIT_BYTES:
        raise ApiError(
            "FILE_TOO_LARGE",
            f"File exceeds the {MAX_JUNIT_BYTES // (1024 * 1024)} MB upload limit.",
            status_code=413,
        )
    try:
        parsed = parse_junit(raw)
    except JUnitParseError as exc:
        raise ApiError("INVALID_JUNIT_FILE", str(exc), status_code=400) from exc

    try:
        result = TestRunResult(
            project=project.strip(),
            run_number=run_number,
            branch=(branch or "main").strip() or "main",
            commit_sha=commit_sha,
            workflow_name=workflow_name,
            environment=environment,
            cases=parsed.cases,
        )
    except ValidationError as exc:
        raise ApiError("VALIDATION_ERROR", f"Invalid run metadata: {exc.errors()}") from exc

    try:
        summary = persist_run(db, result)
    except DuplicateRunError as exc:
        raise ApiError("DUPLICATE_RUN", str(exc), status_code=409) from exc
    except ConflictingDuplicateTestError as exc:
        raise ApiError("CONFLICTING_TEST_RECORDS", str(exc), status_code=400) from exc

    return {
        "run_id": summary.run_id,
        "project": summary.project,
        "run_number": summary.run_number,
        "summary": {
            "total": summary.total,
            "passed": summary.passed,
            "failed": summary.failed,
            "error": summary.error,
            "skipped": summary.skipped,
            "new_tests": summary.new_tests,
            "duplicates": summary.duplicates,
        },
    }
