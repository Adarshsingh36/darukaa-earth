import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.project import Project
from app.models.site import Site
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectDetail, ProjectOut

router = APIRouter(prefix="/api/projects", tags=["projects"])


def _to_project_out(project: Project, db: Session) -> ProjectOut:
    site_count = db.query(func.count(Site.id)).filter(Site.project_id == project.id).scalar() or 0
    return ProjectOut(
        id=project.id,
        name=project.name,
        description=project.description,
        location=project.location,
        start_date=project.start_date,
        created_at=project.created_at,
        created_by=project.created_by,
        site_count=site_count,
    )


@router.get("", response_model=list[ProjectOut])
def list_projects(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    projects = db.query(Project).order_by(Project.created_at.desc()).all()
    return [_to_project_out(p, db) for p in projects]


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = Project(
        name=payload.name,
        description=payload.description,
        location=payload.location,
        start_date=payload.start_date,
        created_by=current_user.id,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return _to_project_out(project, db)


@router.get("/{project_id}", response_model=ProjectDetail)
def get_project(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return _to_project_out(project, db)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if project.created_by != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to delete this project")
    db.delete(project)
    db.commit()
    return None
