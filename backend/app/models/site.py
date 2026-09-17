import uuid
from datetime import UTC, datetime

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Site(Base):
    __tablename__ = "sites"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Polygon geometry stored in WGS84 (SRID 4326), as sent by Mapbox GL Draw GeoJSON.
    geometry = mapped_column(Geometry(geometry_type="POLYGON", srid=4326), nullable=False)

    area_hectares: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    project = relationship("Project", back_populates="sites")
    metrics = relationship(
        "Metric", back_populates="site", cascade="all, delete-orphan", order_by="Metric.recorded_at"
    )
