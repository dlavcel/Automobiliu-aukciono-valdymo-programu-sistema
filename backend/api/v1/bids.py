from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.core.deps import get_current_user, get_db
from backend.models.user import User
from backend.schemas.bid import BidRead, EnglishBidCreate, SealedBidCreate
from backend.services.bid_service import place_english_bid, place_sealed_bid

router = APIRouter(tags=["bids"])

@router.post("/auctions/{auction_id}/bids", response_model=BidRead)
def create_english_bid(
    auction_id: UUID,
    payload: EnglishBidCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return place_english_bid(db, auction_id, current_user, payload.amount)

@router.post("/auctions/{auction_id}/sealed-bids", response_model=BidRead)
def create_sealed_bid(
    auction_id: UUID,
    payload: SealedBidCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return place_sealed_bid(db, auction_id, current_user, payload.amount)