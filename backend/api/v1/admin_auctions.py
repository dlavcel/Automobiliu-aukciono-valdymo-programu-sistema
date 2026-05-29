from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.core.deps import get_db
from backend.schemas.auction import (
    AuctionCreate,
    AuctionDetailRead,
    AuctionRead,
    AuctionStatusResponse,
    AuctionUpdate,
)
from backend.services.auction.auction_service import (
    cancel_auction,
    create_auction,
    get_admin_auction,
    sync_auction_status,
    update_auction,
)

router = APIRouter(prefix="/admin/auctions", tags=["admin-auctions"])

@router.post("", response_model=AuctionRead)
def create_admin_auction(
    payload: AuctionCreate,
    db: Session = Depends(get_db),
):
    return create_auction(db, payload)

@router.get("/{auction_id}", response_model=AuctionDetailRead)
def get_admin_auction_detail(
    auction_id: UUID,
    db: Session = Depends(get_db),
):
    auction = get_admin_auction(db, auction_id)
    return sync_auction_status(db, auction)

@router.put("/{auction_id}", response_model=AuctionRead)
def update_admin_auction(
    auction_id: UUID,
    payload: AuctionUpdate,
    db: Session = Depends(get_db),
):
    auction = get_admin_auction(db, auction_id)
    return update_auction(db, auction, payload)

@router.post("/{auction_id}/cancel", response_model=AuctionStatusResponse)
def cancel_admin_auction(
    auction_id: UUID,
    db: Session = Depends(get_db),
):
    auction = get_admin_auction(db, auction_id)
    auction = cancel_auction(db, auction)

    return AuctionStatusResponse(
        message="Auction cancelled",
        auction_id=auction.id,
        status=auction.status,
    )