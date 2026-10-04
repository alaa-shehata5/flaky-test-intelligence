"""Phase 2 database tests: models, relationships, constraints, identity."""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.models import Project, TestCase, TestExecution, TestRun


@pytest.fixture()
def db() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    session = factory()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def _project(db: Session, name: str = "demo-project") -> Project:
    project = Project(name=name, repository="https://example.com/demo.git")
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def _run(db: Session, project: Project, run_number: int = 1) -> TestRun:
    run = TestRun(project_id=project.id, run_number=run_number, branch="main")
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def _case(
    db: Session,
    project: Project,
    classname: str = "tests.test_auth",
    test_name: str = "test_valid_login",
) -> TestCase:
    unique_key = f"{project.name}::{classname}::{test_name}"
    case = TestCase(
        project_id=project.id,
        suite_name="auth",
        classname=classname,
        test_name=test_name,
        unique_key=unique_key,
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


def test_full_chain_insertion_and_relationships(db: Session):
    project = _project(db)
    run = _run(db, project)
    case = _case(db, project)
    execution = TestExecution(run_id=run.id, test_case_id=case.id, status="passed", duration=0.42)
    db.add(execution)
    db.commit()

    assert execution.id is not None
    assert run.project.id == project.id
    assert case.project.id == project.id
    assert execution.run.id == run.id
    assert execution.test_case.id == case.id
    assert project.runs[0].id == run.id
    assert project.test_cases[0].id == case.id
    assert run.executions[0].status == "passed"
    assert case.executions[0].duration == pytest.approx(0.42)


def test_unique_test_identity_enforced(db: Session):
    project = _project(db)
    _case(db, project)
    duplicate = TestCase(
        project_id=project.id,
        classname="tests.test_auth",
        test_name="test_valid_login",
        unique_key="demo-project::tests.test_auth::test_valid_login",
    )
    db.add(duplicate)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()

    # Same logical test name in a *different* project is a different identity.
    other = _project(db, name="other-project")
    other_case = _case(db, other)
    assert other_case.unique_key == "other-project::tests.test_auth::test_valid_login"


def test_run_number_unique_per_project(db: Session):
    project = _project(db)
    _run(db, project, run_number=7)
    db.add(TestRun(project_id=project.id, run_number=7, branch="main"))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()

    other = _project(db, name="other-project")
    ok = TestRun(project_id=other.id, run_number=7, branch="main")
    db.add(ok)
    db.commit()
    assert ok.id is not None


def test_execution_status_constraint(db: Session):
    project = _project(db)
    run = _run(db, project)
    case = _case(db, project)
    db.add(TestExecution(run_id=run.id, test_case_id=case.id, status="bogus", duration=1.0))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_execution_history_retrieval_ordered(db: Session):
    project = _project(db)
    case = _case(db, project)
    runs = [_run(db, project, run_number=n) for n in (1, 2, 3)]
    for run, status in zip(runs, ["passed", "failed", "passed"], strict=True):
        db.add(TestExecution(run_id=run.id, test_case_id=case.id, status=status, duration=0.5))
    db.commit()

    rows = db.scalars(
        select(TestExecution)
        .where(TestExecution.test_case_id == case.id)
        .order_by(TestExecution.id)
    ).all()
    assert [r.status for r in rows] == ["passed", "failed", "passed"]
    assert all(r.run.project_id == project.id for r in rows)


def test_cascade_delete_project_removes_children(db: Session):
    project = _project(db)
    run = _run(db, project)
    case = _case(db, project)
    db.add(TestExecution(run_id=run.id, test_case_id=case.id, status="failed", duration=2.0))
    db.commit()

    db.delete(project)
    db.commit()
    assert db.scalar(select(TestRun).where(TestRun.id == run.id)) is None
    assert db.scalar(select(TestCase).where(TestCase.id == case.id)) is None
    assert db.scalar(select(TestExecution)) is None
