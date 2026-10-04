"""Runs API: JUnit upload endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, UploadFile
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.api.errors import ApiError
from app.db.session import get_db
from app.ingestion.parser import MAX_JUNIT_BYTES, JUnitParseError, parse_junit
from app.ingestion.schemas import TestRunResult
from app.ingestion.service import DuplicateRunError, persist_run

router = APIRouter(prefix="/api/runs", tags=["runs"])


@router.post("/upload", status_code=201)
def upload_run(
    file: UploadFile = File(...),  # noqa: B008 - canonical FastAPI dependency declaration
    project: str = Form(...),
    run_number: int = Form(...),
    branch: str = Form("main"),
    commit_sha: str | None = Form(None),
    workflow_name: str | None = Form(None),
    environment: str | None = Form(None),
    db: Session = Depends(get_db),  # noqa: B008 - canonical FastAPI dependency declaration
) -> dict:
    filename = (file.filename or "").lower()
    if not filename.endswith(".xml"):
        raise ApiError(
            "INVALID_FILE_TYPE",
            "Only JUnit XML files (.xml) are accepted.",
            status_code=400,
        )
    raw = file.file.read()
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
