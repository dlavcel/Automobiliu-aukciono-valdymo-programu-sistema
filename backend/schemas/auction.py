from datetime import datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, model_validator

from backend.enums.auction_status import AuctionStatus
from backend.enums.auction_type import AuctionType
from backend.enums.sale_type import SaleType
from backend.schemas.listing import ListingRead

class AuctionCreate(BaseModel):
    listing_id: UUID
    starts_at: datetime
    ends_at: datetime

    @model_validator(mode="after")
    def validate_dates(self):
        if self.starts_at.tzinfo is None:
            raise ValueError("starts_at must include timezone, e.g. Z or +03:00")
        if self.ends_at.tzinfo is None:
            raise ValueError("ends_at must include timezone, e.g. Z or +03:00")
        if self.ends_at <= self.starts_at:
            raise ValueError("ends_at must be later than starts_at")
        return self

class AuctionUpdate(BaseModel):
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    status: AuctionStatus | None = None

class AuctionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    listing_id: UUID
    current_price: Decimal | None = None
    starts_at: datetime
    ends_at: datetime
    status: AuctionStatus
    winner_user_id: UUID | None = None
    created_at: datetime
    updated_at: datetime

class AuctionDetailRead(AuctionRead):
    listing: ListingRead
    auction_type: AuctionType
    sale_type: SaleType

class AuctionStatusResponse(BaseModel):
    message: str
    auction_id: UUID
    status: AuctionStatus