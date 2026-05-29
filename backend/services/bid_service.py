from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
import anyio

from backend.enums.auction_status import AuctionStatus
from backend.enums.auction_type import AuctionType
from backend.enums.bid_type import BidType
from backend.models.auction import Auction
from backend.models.bid import Bid
from backend.models.user import User
from backend.services.auction.auction_service import sync_auction_status
from backend.services.auction.auction_ws_manager import auction_ws_manager

def get_auction_for_bidding(db: Session, auction_id: UUID) -> Auction:
    stmt = (
        select(Auction)
        .options(selectinload(Auction.listing))
        .where(Auction.id == auction_id)
        .with_for_update()
    )
    auction = db.scalar(stmt)
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    return auction

def validate_live_auction(auction: Auction) -> None:
    if auction.status != AuctionStatus.LIVE:
        raise HTTPException(status_code=400, detail="Auction is not live")

def place_english_bid(db: Session, auction_id: UUID, bidder: User, amount: Decimal) -> Bid:
    auction = get_auction_for_bidding(db, auction_id)
    auction = sync_auction_status(db, auction)

    if auction.listing.owner_user_id == bidder.id:
        raise HTTPException(status_code=400, detail="You cannot bid on your own listing")

    if auction.auction_type != AuctionType.ENGLISH:
        raise HTTPException(status_code=400, detail="Auction is not english type")

    validate_live_auction(auction)

    current_price = Decimal(auction.current_price or 0)
    min_increment = Decimal(auction.min_increment or 0)

    minimum_allowed = current_price + min_increment
    if amount % 1 != 0:
        raise HTTPException(
            status_code=400,
            detail="Bids must be whole numbers"
        )

    if amount < minimum_allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Bid must be at least {minimum_allowed}"
        )

    bid = Bid(
        auction_id=auction.id,
        bidder_user_id=bidder.id,
        bid_type=BidType.ENGLISH,
        amount=amount,
    )

    auction.current_price = amount

    db.add(bid)
    db.add(auction)
    db.commit()
    db.refresh(bid)

    try:
        anyio.from_thread.run(
            auction_ws_manager.broadcast,
            auction.id,
            {
                "event": "english_bid_placed",
                "auction_id": str(auction.id),
                "current_price": str(auction.current_price),
                "bid_amount": str(bid.amount),
                "bidder_user_id": str(bid.bidder_user_id),
                "status": auction.status.value,
            },
        )
    except Exception as exc:
        print(f"[WS ERROR] {exc}")

    return bid

def place_sealed_bid(db: Session, auction_id: UUID, bidder: User, amount: Decimal) -> Bid:
    auction = get_auction_for_bidding(db, auction_id)
    auction = sync_auction_status(db, auction)

    if auction.listing.owner_user_id == bidder.id:
        raise HTTPException(status_code=400, detail="You cannot bid on your own listing")

    if auction.auction_type != AuctionType.SEALED_FIRST_PRICE:
        raise HTTPException(status_code=400, detail="Auction is not sealed first price type")

    validate_live_auction(auction)

    stmt = (
        select(Bid)
        .where(
            Bid.auction_id == auction.id,
            Bid.bidder_user_id == bidder.id,
            Bid.bid_type == BidType.SEALED,
        )
        .with_for_update()
    )

    existing_bid = db.scalar(stmt)

    now = datetime.now(timezone.utc)

    if existing_bid:
        existing_bid.amount = amount
        existing_bid.submitted_at = now
        existing_bid.updated_at = now

        db.add(existing_bid)
        db.commit()
        db.refresh(existing_bid)
        return existing_bid

    bid = Bid(
        auction_id=auction.id,
        bidder_user_id=bidder.id,
        bid_type=BidType.SEALED,
        amount=amount,
        submitted_at=now,
        created_at=now,
        updated_at=now,
    )

    db.add(bid)
    db.commit()
    db.refresh(bid)
    return bid
