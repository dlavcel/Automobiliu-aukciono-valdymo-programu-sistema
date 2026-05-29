from uuid import UUID
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.enums.sale_result_status import SaleResultStatus
from backend.enums.sale_type import SaleType
from backend.models.auction import Auction
from backend.models.listing import Listing
from backend.models.user import User

def get_user_won_lots(db: Session, user: User):
    stmt = (
        select(Auction)
        .options(
            selectinload(Auction.listing).selectinload(Listing.images)
        )
        .where(
            Auction.winner_user_id == user.id,
            Auction.sale_result_status == SaleResultStatus.SOLD,
        )
        .order_by(Auction.ends_at.desc())
    )
    return list(db.scalars(stmt).all())

def get_user_pending_listing_approvals(db: Session, user: User):
    stmt = (
        select(Auction)
        .options(
            selectinload(Auction.listing).selectinload(Listing.images)
        )
        .join(Listing, Auction.listing_id == Listing.id)
        .where(
            Listing.owner_user_id == user.id,
            Listing.sale_type == SaleType.ON_APPROVAL,
            Auction.sale_type == SaleType.ON_APPROVAL,
            Auction.sale_result_status == SaleResultStatus.AWAITING_SELLER_APPROVAL,
            Auction.winner_user_id.is_not(None),
        )
        .order_by(Auction.ends_at.desc())
    )
    return list(db.scalars(stmt).all())

def get_user_owned_auction_for_approval(db: Session, auction_id: UUID, user: User) -> Auction:
    stmt = (
        select(Auction)
        .options(
            selectinload(Auction.listing).selectinload(Listing.images)
        )
        .join(Listing, Auction.listing_id == Listing.id)
        .where(
            Auction.id == auction_id,
            Listing.owner_user_id == user.id,
        )
    )

    auction = db.scalar(stmt)
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")

    if auction.listing.sale_type != SaleType.ON_APPROVAL:
        raise HTTPException(status_code=400, detail="Listing is not on approval sale type")

    if auction.sale_type != SaleType.ON_APPROVAL:
        raise HTTPException(status_code=400, detail="Auction is not on approval sale type")

    if auction.sale_result_status != SaleResultStatus.AWAITING_SELLER_APPROVAL:
        raise HTTPException(status_code=400, detail="Auction is not awaiting seller approval")

    if auction.winner_user_id is None:
        raise HTTPException(status_code=400, detail="Auction has no winner to approve")

    return auction

def approve_user_listing_auction(db: Session, auction_id: UUID, user: User) -> Auction:
    auction = get_user_owned_auction_for_approval(db, auction_id, user)

    if auction.winner_user_id is None:
        raise HTTPException(status_code=400, detail="Auction has no winner to approve")

    auction.sale_result_status = SaleResultStatus.SOLD

    db.add(auction)
    db.commit()
    db.refresh(auction)
    return auction

def reject_user_listing_auction(db: Session, auction_id: UUID, user: User) -> Auction:
    auction = get_user_owned_auction_for_approval(db, auction_id, user)

    auction.sale_result_status = SaleResultStatus.REJECTED_BY_SELLER
    auction.winner_user_id = None

    db.add(auction)
    db.commit()
    db.refresh(auction)
    return auction