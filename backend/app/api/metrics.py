import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.metric import Metric
from app.models.site import Site
from app.models.user import User
from app.schemas.metric import MetricCreate, MetricOut

router = APIRouter(tags=["metrics"])


@router.get("/api/sites/{site_id}/metrics", response_model=list[MetricOut])
def list_metrics(
    site_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    site = db.get(Site, site_id)
    if not site:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")
    metrics = db.query(Metric).filter(Metric.site_id == site_id).order_by(Metric.recorded_at.asc()).all()
    return metrics


@router.post("/api/sites/{site_id}/metrics", response_model=MetricOut, status_code=status.HTTP_201_CREATED)
def create_metric(
    site_id: uuid.UUID,
    payload: MetricCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    site = db.get(Site, site_id)
    if not site:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")

    metric = Metric(site_id=site_id, **payload.model_dump())
    db.add(metric)
    db.commit()
    db.refresh(metric)
    return metric
