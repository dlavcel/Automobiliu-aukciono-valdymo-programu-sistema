from datetime import datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

from backend.enums.bid_type import BidType

class EnglishBidCreate(BaseModel):
    amount: Decimal = Field(..., gt=0)

class SealedBidCreate(BaseModel):
    amount: Decimal = Field(..., gt=0)

class BidRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    auction_id: UUID
    bidder_user_id: UUID
    bid_type: BidType
    amount: Decimal
    submitted_at: datetime
    created_at: datetime
    updated_at: datetime

class DutchAcceptResponse(BaseModel):
    message: str
    auction_id: UUID
    winning_bid_id: UUID
    final_price: Decimal