from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from backend.core.deps import get_db
from backend.enums.auction_type import AuctionType
from backend.models.auction import Auction
from backend.models.bid import Bid
from backend.schemas.bid import BidRead

router = APIRouter(tags=["auction-history"])

@router.get("/auctions/{auction_id}/bids", response_model=list[BidRead])
def get_auction_bids(
    auction_id: UUID,
    db: Session = Depends(get_db),
):
    auction = db.get(Auction, auction_id)
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")

    if auction.auction_type != AuctionType.ENGLISH:
        raise HTTPException(status_code=400, detail="Bid history is public only for english auctions")

    stmt = (
        select(Bid)
        .where(Bid.auction_id == auction_id)
        .order_by(desc(Bid.created_at))
    )

    return list(db.scalars(stmt).all())