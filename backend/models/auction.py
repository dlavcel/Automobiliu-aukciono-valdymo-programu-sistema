import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import DateTime, Enum as SqlEnum, ForeignKey, Numeric, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base
from backend.enums.auction_status import AuctionStatus
from backend.enums.auction_type import AuctionType
from backend.enums.sale_result_status import SaleResultStatus
from backend.enums.sale_type import SaleType

class Auction(Base):
    __tablename__ = "auctions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    listing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("listings.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
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

    start_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    current_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    min_increment: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)

    price_decrement: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    decrement_interval_seconds: Mapped[int | None] = mapped_column(Integer, default=10)

    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    status: Mapped[AuctionStatus] = mapped_column(
        SqlEnum(AuctionStatus, name="auction_status"),
        nullable=False,
        default=AuctionStatus.SCHEDULED,
        index=True,
    )

    winner_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    listing = relationship("Listing", back_populates="auction")
    bids = relationship(
        "Bid",
        back_populates="auction",
        cascade="all, delete-orphan",
    )

    sale_result_status: Mapped[SaleResultStatus] = mapped_column(
        SqlEnum(SaleResultStatus, name="sale_result_status"),
        nullable=False,
        default=SaleResultStatus.PENDING,
        index=True,
    )