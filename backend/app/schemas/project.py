import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    location: str | None = None
    start_date: date | None = None


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    location: str | None
    start_date: date | None
    created_at: datetime
    created_by: uuid.UUID
    site_count: int = 0


class ProjectDetail(ProjectOut):
    pass
