from datetime import datetime
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.enums.listing_status import ListingStatus
from backend.models.auction import Auction
from backend.models.listing import Listing
from backend.models.user import User

def get_pending_listings(db: Session) -> list[Listing]:
    stmt = (
        select(Listing)
        .options(selectinload(Listing.images))
        .where(Listing.status == ListingStatus.PENDING_REVIEW)
        .order_by(Listing.submitted_at.asc())
    )
    return list(db.scalars(stmt).all())

def get_approved_listings(db: Session) -> list[Listing]:
    stmt = (
        select(Listing)
        .options(selectinload(Listing.images))
        .outerjoin(Auction, Auction.listing_id == Listing.id)
        .where(
            Listing.status == ListingStatus.APPROVED,
            Auction.id.is_(None),
        )
        .order_by(Listing.reviewed_at.desc())
    )

    return list(db.scalars(stmt).all())

def get_admin_listing(db: Session, listing_id: UUID) -> Listing:
    stmt = select(Listing).options(selectinload(Listing.images)).where(Listing.id == listing_id)
    listing = db.scalar(stmt)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return listing

def approve_listing(db: Session, listing: Listing, admin: User) -> Listing:
    if listing.status != ListingStatus.PENDING_REVIEW:
        raise HTTPException(status_code=400, detail="Only pending_review listings can be approved")

    listing.status = ListingStatus.APPROVED
    listing.reviewed_at = datetime.utcnow()
    listing.reviewed_by = admin.id
    listing.rejection_reason = None

    db.add(listing)
    db.commit()
    db.refresh(listing)
    return listing

def reject_listing(db: Session, listing: Listing, admin: User, reason: str) -> Listing:
    if listing.status != ListingStatus.PENDING_REVIEW:
        raise HTTPException(status_code=400, detail="Only pending_review listings can be rejected")

    listing.status = ListingStatus.REJECTED
    listing.reviewed_at = datetime.utcnow()
    listing.reviewed_by = admin.id
    listing.rejection_reason = reason

    db.add(listing)
    db.commit()
    db.refresh(listing)
    return listing