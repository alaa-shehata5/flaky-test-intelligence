"""Persistence service: normalized JUnit results -> PostgreSQL rows."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ingestion.identity import build_unique_key
from app.ingestion.schemas import TestRunResult
from app.models import Project, TestCase, TestExecution, TestRun


class DuplicateRunError(ValueError):
    """Raised when the same (project, run_number) is ingested twice."""


@dataclass
class RunSummary:
    project_id: int
    project: str
    run_id: int
    run_number: int
    total: int
    passed: int
    failed: int
    error: int
    skipped: int
    new_tests: int
    duplicates: int


def persist_run(
    session: Session,
    result: TestRunResult,
    executed_at: datetime | None = None,
) -> RunSummary:
    """Store a parsed run and its executions. Commits on success."""
    now = executed_at or datetime.now(UTC)

    project = session.scalar(select(Project).where(Project.name == result.project))
    if project is None:
        project = Project(name=result.project)
        session.add(project)
        session.flush()

    existing = session.scalar(
        select(TestRun).where(
            TestRun.project_id == project.id, TestRun.run_number == result.run_number
        )
    )
    if existing is not None:
        raise DuplicateRunError(
            f"run {result.run_number} for project '{result.project}' already exists"
        )

    # Deduplicate repeated records of the same logical test: keep first.
    seen: set[tuple[str, str]] = set()
    unique_cases = []
    duplicates = 0
    for case in result.cases:
        key = (case.classname, case.test_name)
        if key in seen:
            duplicates += 1
            continue
        seen.add(key)
        unique_cases.append(case)

    run = TestRun(
        project_id=project.id,
        run_number=result.run_number,
        commit_sha=result.commit_sha,
        branch=result.branch,
        workflow_name=result.workflow_name,
        environment=result.environment,
        started_at=now,
        finished_at=now,
    )
    session.add(run)
    session.flush()

    passed = failed = error = skipped = 0
    total_duration = 0.0
    new_tests = 0
    for case in unique_cases:
        unique_key = build_unique_key(result.project, case.classname, case.test_name)
        test_case = session.scalar(select(TestCase).where(TestCase.unique_key == unique_key))
        if test_case is None:
            test_case = TestCase(
                project_id=project.id,
                suite_name=case.suite_name,
                classname=case.classname,
                test_name=case.test_name,
                unique_key=unique_key,
                first_seen_at=now,
                last_seen_at=now,
            )
            session.add(test_case)
            session.flush()
            new_tests += 1
        else:
            test_case.last_seen_at = now
            if case.suite_name is not None:
                test_case.suite_name = case.suite_name

        session.add(
            TestExecution(
                run_id=run.id,
                test_case_id=test_case.id,
                status=case.status,
                duration=case.duration,
                failure_message=case.failure_message,
                failure_type=case.failure_type,
                executed_at=now,
            )
        )
        total_duration += case.duration
        if case.status == "passed":
            passed += 1
        elif case.status == "failed":
            failed += 1
        elif case.status == "error":
            error += 1
        else:
            skipped += 1

    run.total_tests = len(unique_cases)
    run.passed_tests = passed
    run.failed_tests = failed
    run.error_tests = error
    run.skipped_tests = skipped
    run.total_duration = total_duration

    session.commit()
    session.refresh(run)
    return RunSummary(
        project_id=project.id,
        project=project.name,
        run_id=run.id,
        run_number=run.run_number,
        total=len(unique_cases),
        passed=passed,
        failed=failed,
        error=error,
        skipped=skipped,
        new_tests=new_tests,
        duplicates=duplicates,
    )
