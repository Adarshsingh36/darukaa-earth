import uuid
from datetime import timezone, date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Metric(Base):
    __tablename__ = "metrics"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sites.id"), nullable=False, index=True
    )
    recorded_at: Mapped[date] = mapped_column(Date, nullable=False)
    carbon_tonnes: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    biodiversity_index: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False, default=0)
    tree_cover_percentage: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False, default=0)
    species_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    site = relationship("Site", back_populates="metrics")

