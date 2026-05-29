import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import DateTime, Enum as SqlEnum, ForeignKey, Integer, String, Text, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base
from backend.enums.damage_type import DamageType
from backend.enums.listing_status import ListingStatus
from backend.enums.auction_type import AuctionType
from backend.enums.sale_type import SaleType
from backend.enums.vehicle import FuelType, DriveType, Transmission

class Listing(Base):
    __tablename__ = "listings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    make: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    model: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    vin: Mapped[str | None] = mapped_column(String(17), nullable=True)
    mileage: Mapped[int | None] = mapped_column(Integer, nullable=True)

    fuel_type = mapped_column(SqlEnum(FuelType), nullable=True)
    engine_volume: Mapped[float | None] = mapped_column(Numeric(2, 1), nullable=True)
    cylinders: Mapped[int | None] = mapped_column(Integer, nullable=True)
    drive_type = mapped_column(SqlEnum(DriveType), nullable=True)
    transmission = mapped_column(SqlEnum(Transmission), nullable=True)
    body_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    color: Mapped[str | None] = mapped_column(String(50), nullable=True)

    primary_damage: Mapped[DamageType | None] = mapped_column(
        SqlEnum(DamageType, name="damage_type"),
        nullable=True,
    )
    secondary_damage: Mapped[DamageType | None] = mapped_column(
        SqlEnum(DamageType, name="damage_type"),
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)

    status: Mapped[ListingStatus] = mapped_column(
        SqlEnum(ListingStatus, name="listing_status"),
        nullable=False,
        default=ListingStatus.DRAFT,
        index=True,
    )

    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    submitted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    images: Mapped[list["ListingImage"]] = relationship(
        "ListingImage",
        back_populates="listing",
        cascade="all, delete-orphan",
        order_by="ListingImage.sort_order",
    )

    auction: Mapped["Auction | None"] = relationship(
        "Auction",
        back_populates="listing",
        uselist=False,
    )

    auction_type: Mapped[AuctionType] = mapped_column(
        SqlEnum(AuctionType, name="auction_type"),
        nullable=False,
        index=True,
    )

    sale_type: Mapped[SaleType] = mapped_column(
        SqlEnum(SaleType, name="sale_type"),
        nullable=False,
        index=True,
    )

    reserve_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)

    cv_result: Mapped["ListingCVResult | None"] = relationship(
        "ListingCVResult",
        back_populates="listing",
        uselist=False,
        cascade="all, delete-orphan",
    )

    price_prediction: Mapped["ListingPricePrediction | None"] = relationship(
        "ListingPricePrediction",
        back_populates="listing",
        uselist=False,
        cascade="all, delete-orphan",
    )

    @property
    def primary_damage_severity(self):
        return self.cv_result.primary_damage_severity if self.cv_result else None

    @property
    def secondary_damage_severity(self):
        return self.cv_result.secondary_damage_severity if self.cv_result else None

    @property
    def predicted_price(self):
        return self.price_prediction.predicted_price if self.price_prediction else None