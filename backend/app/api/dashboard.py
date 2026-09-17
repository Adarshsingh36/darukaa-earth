from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.metric import Metric
from app.models.project import Project
from app.models.site import Site
from app.models.user import User
from app.schemas.dashboard import DashboardSummary

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    total_projects = (
        db.query(func.count(Project.id))
        .filter(Project.created_by == current_user.id)
        .scalar()
        or 0
    )

    # Only include sites belonging to the user's projects.
    total_sites = (
        db.query(func.count(Site.id))
        .join(Project, Site.project_id == Project.id)
        .filter(Project.created_by == current_user.id)
        .scalar()
        or 0
    )

    total_area = (
        db.query(func.coalesce(func.sum(Site.area_hectares), 0))
        .join(Project, Site.project_id == Project.id)
        .filter(Project.created_by == current_user.id)
        .scalar()
        or 0
    )

    # Find the most recent measurement for each site belonging
    # to the authenticated user's projects.
    latest_metric_subq = (
        db.query(
            Metric.site_id,
            func.max(Metric.recorded_at).label("latest_date"),
        )
        .join(Site, Metric.site_id == Site.id)
        .join(Project, Site.project_id == Project.id)
        .filter(Project.created_by == current_user.id)
        .group_by(Metric.site_id)
        .subquery()
    )

    latest_metrics = (
        db.query(Metric)
        .join(
            latest_metric_subq,
            (Metric.site_id == latest_metric_subq.c.site_id)
            & (Metric.recorded_at == latest_metric_subq.c.latest_date),
        )
        .all()
    )

    total_carbon = sum(float(m.carbon_tonnes) for m in latest_metrics)

    avg_biodiversity = (
        sum(float(m.biodiversity_index) for m in latest_metrics)
        / len(latest_metrics)
        if latest_metrics
        else 0.0
    )

    return DashboardSummary(
        total_projects=total_projects,
        total_sites=total_sites,
        total_area_hectares=round(float(total_area), 2),
        total_carbon_tonnes=round(total_carbon, 2),
        average_biodiversity_index=round(avg_biodiversity, 2),
    )
