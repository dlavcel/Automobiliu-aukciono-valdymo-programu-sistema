from sqlalchemy import desc, select, asc
from sqlalchemy.orm import Session

from backend.enums.auction_status import AuctionStatus
from backend.enums.auction_type import AuctionType
from backend.enums.bid_type import BidType
from backend.enums.sale_result_status import SaleResultStatus
from backend.models.auction import Auction
from backend.models.bid import Bid

def resolve_sealed_first_price_auction(db: Session, auction: Auction) -> Auction:
    if auction.auction_type != AuctionType.SEALED_FIRST_PRICE:
        return auction

    if auction.status != AuctionStatus.ENDED:
        return auction

    if auction.winner_user_id is not None:
        return auction

    stmt = (
        select(Bid)
        .where(
            Bid.auction_id == auction.id,
            Bid.bid_type == BidType.SEALED,
        )
        .order_by(
            desc(Bid.amount),
            asc(Bid.submitted_at),
            asc(Bid.created_at),
            asc(Bid.id),
        )
    )

    winning_bid = db.scalars(stmt).first()

    if not winning_bid:
        auction.sale_result_status = SaleResultStatus.RESERVE_NOT_MET
        auction.winner_user_id = None
        auction.current_price = None

        db.add(auction)
        db.commit()
        db.refresh(auction)

        return auction

    auction.winner_user_id = winning_bid.bidder_user_id
    auction.current_price = winning_bid.amount

    db.add(auction)
    db.commit()
    db.refresh(auction)
    return auction