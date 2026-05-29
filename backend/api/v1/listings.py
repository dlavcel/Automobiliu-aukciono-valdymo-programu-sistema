from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, File, UploadFile
from sqlalchemy.orm import Session

from backend.core.deps import get_current_user, get_db
from backend.models.user import User
from backend.schemas.listing import (
    ListingCreate,
    ListingImageAnalyzeResponse,
    ListingPricePredictRequest,
    ListingPricePredictResponse,
    ListingRead,
    ListingSubmitResponse,
    ListingUpdate,
)
from backend.services.listing_service import (
    analyze_listing_image,
    create_listing,
    delete_user_listing_image,
    get_listing_for_owner,
    get_listing_public_or_owned_or_admin,
    get_my_listings,
    predict_listing_price,
    submit_user_listing,
    update_listing,
    upload_listing_image,
)

router = APIRouter(tags=["listings"])

@router.post("/listings", response_model=ListingRead)
def create_user_listing(
    payload: ListingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_listing(db, current_user, payload)

@router.post("/listings/{listing_id}/submit", response_model=ListingSubmitResponse, status_code=202)
def submit_user_listing_endpoint(
    listing_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return submit_user_listing(db, listing_id, current_user, background_tasks)

@router.patch("/listings/{listing_id}", response_model=ListingRead)
def update_user_listing(
    listing_id: UUID,
    payload: ListingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    listing = get_listing_for_owner(db, listing_id, current_user.id)
    return update_listing(db, listing, payload)

@router.get("/my/listings", response_model=list[ListingRead])
def get_my_listings_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_my_listings(db, current_user)

@router.get("/listings/{listing_id}", response_model=ListingRead)
def get_listing(
    listing_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_listing_public_or_owned_or_admin(db, listing_id, current_user)

@router.post("/listings/{listing_id}/images/upload")
async def upload_listing_image_endpoint(
    listing_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await upload_listing_image(db, listing_id, current_user, file)

@router.post(
    "/listings/{listing_id}/images/{image_id}/analyze",
    response_model=ListingImageAnalyzeResponse,
)
def analyze_user_listing_image(
    listing_id: UUID,
    image_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return analyze_listing_image(db, listing_id, image_id, current_user)

@router.delete("/listings/{listing_id}/images/{image_id}", status_code=204)
def delete_user_listing_image_endpoint(
    listing_id: UUID,
    image_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    delete_user_listing_image(db, listing_id, image_id, current_user)

@router.post(
    "/listings/{listing_id}/predict-price",
    response_model=ListingPricePredictResponse,
)
def predict_user_listing_price(
    listing_id: UUID,
    payload: ListingPricePredictRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return predict_listing_price(db, listing_id, payload, current_user)
