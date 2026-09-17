import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class GeoJSONPolygon(BaseModel):
    """Minimal GeoJSON Polygon geometry, as produced by Mapbox GL Draw."""

    type: str = "Polygon"
    coordinates: list[list[list[float]]]

    @field_validator("type")
    @classmethod
    def type_must_be_polygon(cls, v: str) -> str:
        if v != "Polygon":
            raise ValueError("geometry.type must be 'Polygon'")
        return v

    @field_validator("coordinates")
    @classmethod
    def validate_ring(cls, v: list[list[list[float]]]) -> list[list[list[float]]]:
        if not v or not v[0]:
            raise ValueError("Polygon must contain at least one linear ring")
        ring = v[0]
        if len(ring) < 4:
            raise ValueError("Polygon ring must have at least 4 positions (closed ring)")
        if ring[0] != ring[-1]:
            raise ValueError("Polygon ring must be closed (first and last positions equal)")
        for position in ring:
            if len(position) < 2:
                raise ValueError("Each coordinate must have at least [lng, lat]")
            lng, lat = position[0], position[1]
            if not (-180 <= lng <= 180) or not (-90 <= lat <= 90):
                raise ValueError("Coordinates out of valid lng/lat range")
        return v


class SiteCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    geometry: GeoJSONPolygon


class SiteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    description: str | None
    geometry: Any  # returned as GeoJSON dict
    area_hectares: float
    created_at: datetime
