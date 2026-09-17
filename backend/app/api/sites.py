import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.project import Project
from app.models.site import Site
from app.models.user import User
from app.schemas.site import SiteCreate, SiteOut
from app.services.geo import calculate_area_hectares, geojson_to_ewkt_element, geometry_to_geojson

router = APIRouter(tags=["sites"])


def _to_site_out(site: Site) -> SiteOut:
    return SiteOut(
        id=site.id,
        project_id=site.project_id,
        name=site.name,
        description=site.description,
        geometry=geometry_to_geojson(site.geometry),
        area_hectares=float(site.area_hectares),
        created_at=site.created_at,
    )


@router.get("/api/projects/{project_id}/sites", response_model=list[SiteOut])
def list_sites_for_project(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    sites = db.query(Site).filter(Site.project_id == project_id).order_by(Site.created_at.desc()).all()
    return [_to_site_out(s) for s in sites]


@router.post(
    "/api/projects/{project_id}/sites",
    response_model=SiteOut,
    status_code=status.HTTP_201_CREATED,
)
def create_site(
    project_id: uuid.UUID,
    payload: SiteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    try:
        geom_element = geojson_to_ewkt_element(payload.geometry.model_dump())
    except Exception as exc:  # invalid geometry from client
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Invalid polygon geometry: {exc}"
        ) from exc

    site = Site(
        project_id=project_id,
        name=payload.name,
        description=payload.description,
        geometry=geom_element,
    )
    db.add(site)
    db.flush()  # geometry needs to be persisted before ST_Area can read it back reliably

    site.area_hectares = calculate_area_hectares(db, site.geometry)
    db.commit()
    db.refresh(site)
    return _to_site_out(site)


@router.get("/api/sites/{site_id}", response_model=SiteOut)
def get_site(
    site_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    site = db.get(Site, site_id)
    if not site:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")
    return _to_site_out(site)


@router.delete("/api/sites/{site_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_site(
    site_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    site = db.get(Site, site_id)
    if not site:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")
    db.delete(site)
    db.commit()
    return None
