import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class MetricCreate(BaseModel):
    recorded_at: date
    carbon_tonnes: float = Field(ge=0)
    biodiversity_index: float = Field(ge=0, le=100)
    tree_cover_percentage: float = Field(ge=0, le=100)
    species_count: int = Field(ge=0)


class MetricOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    site_id: uuid.UUID
    recorded_at: date
    carbon_tonnes: float
    biodiversity_index: float
    tree_cover_percentage: float
    species_count: int
    created_at: datetime
