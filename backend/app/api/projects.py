"""Projects API."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.common import get_project_or_404
from app.api.errors import ApiError
from app.api.schemas import ProjectCreate, ProjectListOut, ProjectOut
from app.db.session import get_db
from app.models import Project, TestCase, TestRun

router = APIRouter(prefix="/api/projects", tags=["projects"])


def _to_out(session: Session, project: Project) -> ProjectOut:
    run_count = session.scalar(
        select(func.count()).select_from(TestRun).where(TestRun.project_id == project.id)
    )
    test_count = session.scalar(
        select(func.count()).select_from(TestCase).where(TestCase.project_id == project.id)
    )
    return ProjectOut(
        id=project.id,
        name=project.name,
        repository=project.repository,
        created_at=project.created_at,
        run_count=run_count or 0,
        test_count=test_count or 0,
    )


@router.get("", response_model=ProjectListOut)
def list_projects(db: Session = Depends(get_db)) -> ProjectListOut:  # noqa: B008
    projects = list(db.scalars(select(Project).order_by(Project.id)))
    return ProjectListOut(items=[_to_out(db, p) for p in projects], total=len(projects))


@router.post("", response_model=ProjectOut, status_code=201)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)) -> ProjectOut:  # noqa: B008
    name = payload.name.strip()
    if not name:
        raise ApiError("VALIDATION_ERROR", "project name must not be blank", 400)
    project = Project(name=name, repository=payload.repository)
    db.add(project)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ApiError("PROJECT_EXISTS", f"project '{name}' already exists", 409) from exc
    db.refresh(project)
    return _to_out(db, project)


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: int, db: Session = Depends(get_db)) -> ProjectOut:  # noqa: B008
    return _to_out(db, get_project_or_404(db, project_id))
