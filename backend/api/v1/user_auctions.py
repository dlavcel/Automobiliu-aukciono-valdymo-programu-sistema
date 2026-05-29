from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.core.deps import get_current_user, get_db
from backend.models.user import User
from backend.schemas.auction import AuctionDetailRead
from backend.services.user_auction_service import (
    approve_user_listing_auction,
    get_user_pending_listing_approvals,
    get_user_won_lots,
    reject_user_listing_auction,
)

router = APIRouter(prefix="/users/me", tags=["user-auctions"])

@router.get("/won-lots", response_model=list[AuctionDetailRead])
def user_won_lots(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_user_won_lots(db, current_user)

@router.get("/pending-approvals", response_model=list[AuctionDetailRead])
def user_pending_approvals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_user_pending_listing_approvals(db, current_user)

@router.post("/auctions/{auction_id}/approve", response_model=AuctionDetailRead)
def approve_listing_auction(
    auction_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return approve_user_listing_auction(db, auction_id, current_user)

@router.post("/auctions/{auction_id}/reject", response_model=AuctionDetailRead)
def reject_listing_auction(
    auction_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return reject_user_listing_auction(db, auction_id, current_user)