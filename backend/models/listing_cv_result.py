import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base

class ListingCVResult(Base):
    __tablename__ = "listing_cv_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    listing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("listings.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    primary_damage_severity: Mapped[Decimal | None] = mapped_column(Numeric(3, 1), nullable=True)
    secondary_damage_severity: Mapped[Decimal | None] = mapped_column(Numeric(3, 1), nullable=True)

    status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    listing: Mapped["Listing"] = relationship(
        "Listing",
        back_populates="cv_result",
    )