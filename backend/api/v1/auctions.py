from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.core.deps import get_db
from backend.enums.auction_status import AuctionStatus
from backend.schemas.auction import AuctionDetailRead
from backend.services.auction.auction_service import (
    get_auction_by_id,
    get_public_auctions,
    sync_auction_status, finalize_auction_state,
)

router = APIRouter(prefix="/auctions", tags=["auctions"])

@router.get("", response_model=list[AuctionDetailRead])
def list_auctions(
    db: Session = Depends(get_db),
    status: AuctionStatus | None = Query(default=None),
    make: str | None = Query(default=None),
    model: str | None = Query(default=None),
):
    auctions = get_public_auctions(db, status=status, make=make, model=model)

    synced = []
    for auction in auctions:
        auction = sync_auction_status(db, auction)
        auction = finalize_auction_state(db, auction)
        synced.append(auction)

    return synced

@router.get("/{auction_id}", response_model=AuctionDetailRead)
def get_auction(auction_id: UUID, db: Session = Depends(get_db)):
    auction = get_auction_by_id(db, auction_id)
    auction = sync_auction_status(db, auction)
    auction = finalize_auction_state(db, auction)
    return auction