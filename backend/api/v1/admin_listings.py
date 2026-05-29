from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.core.deps import get_db, require_admin
from backend.models.user import User
from backend.schemas.listing import ListingRead, ListingRejectRequest
from backend.services.moderation_service import (
    approve_listing,
    get_admin_listing,
    get_pending_listings,
    reject_listing, get_approved_listings,
)

router = APIRouter(prefix="/admin/listings", tags=["admin-listings"])

@router.get("/pending", response_model=list[ListingRead])
def get_pending(
    db: Session = Depends(get_db),
):
    return get_pending_listings(db)

@router.get("/approved", response_model=list[ListingRead])
def get_approved(
    db: Session = Depends(get_db),
):
   return get_approved_listings(db)

@router.get("/{listing_id}", response_model=ListingRead)
def get_one_admin_listing(
    listing_id: UUID,
    db: Session = Depends(get_db),
):
    return get_admin_listing(db, listing_id)

@router.post("/{listing_id}/approve", response_model=ListingRead)
def approve_one_listing(
    listing_id: UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    listing = get_admin_listing(db, listing_id)
    return approve_listing(db, listing, admin)

@router.post("/{listing_id}/reject", response_model=ListingRead)
def reject_one_listing(
    listing_id: UUID,
    payload: ListingRejectRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    listing = get_admin_listing(db, listing_id)
    return reject_listing(db, listing, admin, payload.reason)
