from datetime import datetime, timezone
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.enums.auction_status import AuctionStatus
from backend.enums.auction_type import AuctionType
from backend.enums.listing_status import ListingStatus
from backend.enums.sale_result_status import SaleResultStatus
from backend.enums.sale_type import SaleType
from backend.models.auction import Auction
from backend.models.listing import Listing
from backend.schemas.auction import AuctionUpdate
from backend.services.auction.english_resolution_service import resolve_english_auction
from backend.services.auction.sealed_resolution_service import resolve_sealed_first_price_auction

def create_auction(db: Session, payload) -> Auction:
    listing = db.scalar(select(Listing).where(Listing.id == payload.listing_id))
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    if listing.status != ListingStatus.APPROVED:
        raise HTTPException(status_code=400, detail="Auction can only be created for approved listing")

    existing_auction = db.scalar(select(Auction).where(Auction.listing_id == listing.id))
    if existing_auction:
        raise HTTPException(status_code=400, detail="Auction already exists for this listing")

    if payload.ends_at <= payload.starts_at:
        raise HTTPException(status_code=400, detail="ends_at must be later than starts_at")

    auction = Auction(
        listing_id=listing.id,
        auction_type=listing.auction_type,
        sale_type=listing.sale_type,
        reserve_price=listing.reserve_price,
        start_price=1,
        current_price=1,
        min_increment=1,
        starts_at=payload.starts_at,
        ends_at=payload.ends_at,
        status=AuctionStatus.SCHEDULED,
    )

    db.add(auction)
    db.commit()
    db.refresh(auction)
    return auction

def get_public_auctions(
    db: Session,
    status: AuctionStatus | None = None,
    make: str | None = None,
    model: str | None = None,
):
    stmt = (
        select(Auction)
        .options(
            selectinload(Auction.listing).selectinload(Listing.images),
            selectinload(Auction.listing).selectinload(Listing.cv_result),
            selectinload(Auction.listing).selectinload(Listing.price_prediction),
        )
        .join(Listing, Auction.listing_id == Listing.id)
        .where(Listing.status == ListingStatus.APPROVED)
        .order_by(Auction.created_at.desc())
    )

    if status:
        stmt = stmt.where(Auction.status == status)
    else:
        stmt = stmt.where(Auction.status.in_([
            AuctionStatus.SCHEDULED,
            AuctionStatus.LIVE,
        ]))

    if make:
        stmt = stmt.where(Listing.make.ilike(f"%{make}%"))
    if model:
        stmt = stmt.where(Listing.model.ilike(f"%{model}%"))

    return list(db.scalars(stmt).all())

def get_auction_by_id(db: Session, auction_id: UUID) -> Auction:
    stmt = (
        select(Auction)
        .options(
            selectinload(Auction.listing).selectinload(Listing.images),
            selectinload(Auction.listing).selectinload(Listing.cv_result),
            selectinload(Auction.listing).selectinload(Listing.price_prediction),
        )
        .where(Auction.id == auction_id)
    )
    auction = db.scalar(stmt)
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")

    if auction.listing.status != ListingStatus.APPROVED:
        raise HTTPException(status_code=404, detail="Auction not found")

    return auction

def get_admin_auction(db: Session, auction_id: UUID) -> Auction:
    stmt = (
        select(Auction)
        .options(
            selectinload(Auction.listing).selectinload(Listing.images)
        )
        .where(Auction.id == auction_id)
    )
    auction = db.scalar(stmt)
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    return auction

def cancel_auction(db: Session, auction: Auction) -> Auction:
    if auction.status == AuctionStatus.ENDED:
        raise HTTPException(status_code=400, detail="Ended auction cannot be cancelled")

    auction.status = AuctionStatus.CANCELLED
    db.add(auction)
    db.commit()
    db.refresh(auction)
    return auction

def refresh_auction_status(auction):
    now = datetime.now(timezone.utc)

    starts_at = auction.starts_at
    ends_at = auction.ends_at

    if starts_at.tzinfo is None or ends_at.tzinfo is None:
        raise ValueError("Auction datetimes must be timezone-aware")

    if auction.status in {AuctionStatus.CANCELLED, AuctionStatus.ENDED}:
        return auction

    if now < starts_at:
        auction.status = AuctionStatus.SCHEDULED
    elif starts_at <= now < ends_at:
        auction.status = AuctionStatus.LIVE
    else:
        auction.status = AuctionStatus.ENDED

    return auction

def sync_auction_status(db: Session, auction: Auction) -> Auction:
    old_status = auction.status
    auction = refresh_auction_status(auction)

    if auction.status != old_status:
        db.add(auction)
        db.commit()
        db.refresh(auction)

    return auction

def finalize_auction_state(db: Session, auction: Auction) -> Auction:
    if auction.status != AuctionStatus.ENDED:
        return auction

    if auction.auction_type == AuctionType.SEALED_FIRST_PRICE:
        auction = resolve_sealed_first_price_auction(db, auction)

    if auction.auction_type == AuctionType.ENGLISH:
        auction = resolve_english_auction(db, auction)

    changed = False

    if auction.sale_type == SaleType.PURE_SALE:
        if (
            auction.winner_user_id is not None
            and auction.sale_result_status != SaleResultStatus.SOLD
        ):
            auction.sale_result_status = SaleResultStatus.SOLD
            changed = True

    elif auction.sale_type == SaleType.RESERVE_PRICE:
        if auction.current_price is None or auction.reserve_price is None:
            if (
                auction.sale_result_status != SaleResultStatus.RESERVE_NOT_MET
                or auction.winner_user_id is not None
            ):
                auction.sale_result_status = SaleResultStatus.RESERVE_NOT_MET
                auction.winner_user_id = None
                changed = True
        else:
            if auction.current_price >= auction.reserve_price:
                if auction.sale_result_status != SaleResultStatus.SOLD:
                    auction.sale_result_status = SaleResultStatus.SOLD
                    changed = True
            else:
                if (
                    auction.sale_result_status != SaleResultStatus.RESERVE_NOT_MET
                    or auction.winner_user_id is not None
                ):
                    auction.sale_result_status = SaleResultStatus.RESERVE_NOT_MET
                    auction.winner_user_id = None
                    changed = True

    elif auction.sale_type == SaleType.ON_APPROVAL:

        if (
            auction.winner_user_id is not None
            and auction.sale_result_status != SaleResultStatus.AWAITING_SELLER_APPROVAL
        ):
            auction.sale_result_status = SaleResultStatus.AWAITING_SELLER_APPROVAL
            changed = True

    if changed:
        db.add(auction)
        db.commit()
        db.refresh(auction)

    return auction

def sync_expired_auctions(db: Session) -> int:
    stmt = select(Auction).where(
        Auction.status.in_([AuctionStatus.SCHEDULED, AuctionStatus.LIVE])
    )

    auctions = list(db.scalars(stmt).all())
    updated_count = 0

    for auction in auctions:
        print(f"[DEBUG] checking auction {auction.id}, status={auction.status}")

        old_status = auction.status
        auction = sync_auction_status(db, auction)

        if auction.status != old_status:
            updated_count += 1

        auction = finalize_auction_state(db, auction)

        print(
            f"[DEBUG] finalized auction {auction.id}, "
            f"status={auction.status}, winner={auction.winner_user_id}"
        )

    return updated_count

def update_auction(db: Session, auction: Auction, payload: AuctionUpdate) -> Auction:
    auction = sync_auction_status(db, auction)

    if auction.status != AuctionStatus.SCHEDULED:
        raise HTTPException(
            status_code=400,
            detail="Auction can only be edited before it starts",
        )

    if payload.starts_at is not None:
        auction.starts_at = payload.starts_at

    if payload.ends_at is not None:
        auction.ends_at = payload.ends_at

    if (
        payload.starts_at is not None
        and payload.ends_at is not None
        and payload.ends_at <= payload.starts_at
    ):
        raise HTTPException(status_code=400, detail="ends_at must be later than starts_at")

    auction.start_price = 1
    auction.min_increment = 1

    db.add(auction)
    db.commit()
    db.refresh(auction)
    return auction
