from datetime import datetime
from pathlib import Path
from uuid import UUID, uuid4
from fastapi import BackgroundTasks, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.cv.pipeline import analyze_single_listing_image
from backend.enums.listing_status import ListingStatus
from backend.enums.sale_type import SaleType
from backend.models.listing import Listing
from backend.models.listing_image import ListingImage
from backend.models.user import User
from backend.schemas.listing import (
    ListingImageAnalyzeResponse,
    ListingPricePredictRequest,
    ListingPricePredictResponse,
    ListingRead,
    ListingSubmitResponse,
)
from backend.services.listing_cv_service import (
    run_listing_cv_analysis,
    run_listing_cv_analysis_by_id,
)
from backend.services.price_prediction_service import run_price_prediction

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

def listing_load_options():
    return (
        selectinload(Listing.images),
        selectinload(Listing.auction),
        selectinload(Listing.cv_result),
        selectinload(Listing.price_prediction),
    )

def map_listing_to_read(listing: Listing) -> ListingRead:
    return ListingRead(
        id=listing.id,
        owner_user_id=listing.owner_user_id,
        title=listing.title,
        make=listing.make,
        model=listing.model,
        year=listing.year,
        auction_type=listing.auction_type,
        sale_type=listing.sale_type,
        reserve_price=listing.reserve_price,
        vin=listing.vin,
        mileage=listing.mileage,
        fuel_type=listing.fuel_type,
        engine_volume=float(listing.engine_volume) if listing.engine_volume is not None else None,
        cylinders=listing.cylinders,
        drive_type=listing.drive_type,
        transmission=listing.transmission,
        body_type=listing.body_type,
        color=listing.color,
        primary_damage=listing.primary_damage,
        secondary_damage=listing.secondary_damage,
        description=listing.description,
        location=listing.location,
        primary_damage_severity=listing.cv_result.primary_damage_severity if listing.cv_result else None,
        secondary_damage_severity=listing.cv_result.secondary_damage_severity if listing.cv_result else None,
        predicted_price=listing.price_prediction.predicted_price if listing.price_prediction else None,
        status=listing.status,
        rejection_reason=listing.rejection_reason,
        submitted_at=listing.submitted_at,
        reviewed_at=listing.reviewed_at,
        reviewed_by=listing.reviewed_by,
        created_at=listing.created_at,
        updated_at=listing.updated_at,
        images=listing.images,
    )

def create_listing(db: Session, owner: User, payload) -> Listing:
    listing = Listing(
        owner_user_id=owner.id,
        title=payload.title,
        make=payload.make,
        model=payload.model,
        year=payload.year,
        auction_type=payload.auction_type,
        sale_type=payload.sale_type,
        reserve_price=payload.reserve_price,
        vin=payload.vin,
        mileage=payload.mileage,
        fuel_type=payload.fuel_type,
        engine_volume=payload.engine_volume,
        cylinders=payload.cylinders,
        drive_type=payload.drive_type,
        transmission=payload.transmission,
        body_type=payload.body_type,
        color=payload.color,
        primary_damage=payload.primary_damage,
        secondary_damage=payload.secondary_damage,
        description=payload.description,
        location=payload.location,
        status=ListingStatus.DRAFT,
    )
    db.add(listing)
    db.commit()
    db.refresh(listing)
    return listing

def get_listing_for_owner(db: Session, listing_id: UUID, owner_id: UUID) -> Listing:
    stmt = (
        select(Listing)
        .options(*listing_load_options())
        .where(Listing.id == listing_id, Listing.owner_user_id == owner_id)
    )
    listing = db.scalar(stmt)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return listing

def get_listing_public_or_owned_or_admin(
    db: Session,
    listing_id: UUID,
    current_user: User | None = None,
) -> Listing:
    stmt = (
        select(Listing)
        .options(*listing_load_options())
        .where(Listing.id == listing_id)
    )
    listing = db.scalar(stmt)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    if listing.status == ListingStatus.APPROVED:
        return listing

    if current_user and (current_user.is_admin or listing.owner_user_id == current_user.id):
        return listing

    raise HTTPException(status_code=404, detail="Listing not found")

def get_my_listings(db: Session, owner: User) -> list[Listing]:
    stmt = (
        select(Listing)
        .options(*listing_load_options())
        .where(Listing.owner_user_id == owner.id)
        .order_by(Listing.created_at.desc())
    )
    return list(db.scalars(stmt).all())

def update_listing(db: Session, listing: Listing, payload) -> Listing:
    if listing.status not in {ListingStatus.DRAFT, ListingStatus.REJECTED}:
        raise HTTPException(status_code=400, detail="Only draft or rejected listings can be edited")

    update_data = payload.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(listing, field, value)

    if any(field in update_data for field in {"primary_damage", "secondary_damage"}):
        reset_listing_cv_result(listing)

    db.add(listing)
    db.commit()
    db.refresh(listing)
    return get_listing_for_owner(db, listing.id, listing.owner_user_id)


def reset_listing_cv_result(listing: Listing) -> None:
    if not listing.cv_result:
        return

    listing.cv_result.primary_damage_severity = None
    listing.cv_result.secondary_damage_severity = None
    listing.cv_result.status = None
    listing.cv_result.error = None
    listing.cv_result.processed_at = None

def add_listing_image(db: Session, listing: Listing, image_url: str, sort_order: int = 0) -> ListingImage:
    if listing.status not in {ListingStatus.DRAFT, ListingStatus.REJECTED}:
        raise HTTPException(status_code=400, detail="Cannot edit images for this listing status")

    image = ListingImage(
        listing_id=listing.id,
        image_url=image_url,
        sort_order=sort_order,
    )

    reset_listing_cv_result(listing)
    if listing.cv_result:
        db.add(listing.cv_result)

    db.add(image)
    db.commit()
    db.refresh(image)
    return image

async def upload_listing_image(
    db: Session,
    listing_id: UUID,
    current_user: User,
    file: UploadFile,
) -> dict[str, str]:
    listing = get_listing_for_owner(db, listing_id, current_user.id)

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are allowed")

    ext = Path(file.filename).suffix.lower() if file.filename else ".jpg"
    filename = f"{uuid4()}{ext}"
    file_path = UPLOAD_DIR / filename

    contents = await file.read()
    file_path.write_bytes(contents)

    image = add_listing_image(
        db=db,
        listing=listing,
        image_url=f"/uploads/{filename}",
        sort_order=0,
    )

    return {
        "id": str(image.id),
        "image_url": image.image_url,
    }

def delete_listing_image(db: Session, listing: Listing, image_id: UUID) -> None:
    if listing.status not in {ListingStatus.DRAFT, ListingStatus.REJECTED}:
        raise HTTPException(status_code=400, detail="Cannot edit images for this listing status")

    stmt = select(ListingImage).where(
        ListingImage.id == image_id,
        ListingImage.listing_id == listing.id,
    )
    image = db.scalar(stmt)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    reset_listing_cv_result(listing)
    if listing.cv_result:
        db.add(listing.cv_result)

    db.delete(image)
    db.commit()

def delete_user_listing_image(
    db: Session,
    listing_id: UUID,
    image_id: UUID,
    current_user: User,
) -> None:
    listing = get_listing_for_owner(db, listing_id, current_user.id)
    delete_listing_image(db, listing, image_id)

def validate_listing_before_submit(listing: Listing) -> None:
    missing_fields = []

    if not listing.title:
        missing_fields.append("title")
    if not listing.make:
        missing_fields.append("make")
    if not listing.model:
        missing_fields.append("model")
    if not listing.year:
        missing_fields.append("year")
    if not listing.auction_type:
        missing_fields.append("auction_type")
    if not listing.sale_type:
        missing_fields.append("sale_type")
    if listing.sale_type == SaleType.RESERVE_PRICE and not listing.reserve_price:
        missing_fields.append("reserve_price")
    if not listing.description:
        missing_fields.append("description")
    if not listing.location:
        missing_fields.append("location")
    if not listing.images:
        missing_fields.append("at least one image")

    if missing_fields:
        raise HTTPException(
            status_code=400,
            detail=f"Listing is incomplete. Missing: {', '.join(missing_fields)}",
        )

def submit_listing_for_review(
    db: Session,
    listing: Listing,
    background_tasks: BackgroundTasks,
) -> Listing:
    if listing.status not in {ListingStatus.DRAFT, ListingStatus.REJECTED}:
        raise HTTPException(status_code=400, detail="Only draft or rejected listings can be submitted")

    validate_listing_before_submit(listing)

    listing.status = ListingStatus.PENDING_REVIEW
    listing.submitted_at = datetime.utcnow()
    listing.rejection_reason = None

    if listing.cv_result:
        listing.cv_result.status = "pending"
        listing.cv_result.error = None

    db.add(listing)
    db.commit()
    db.refresh(listing)

    background_tasks.add_task(run_listing_cv_analysis_by_id, listing.id)

    return get_listing_for_owner(db, listing.id, listing.owner_user_id)

def submit_user_listing(
    db: Session,
    listing_id: UUID,
    current_user: User,
    background_tasks: BackgroundTasks,
) -> ListingSubmitResponse:
    listing = get_listing_for_owner(db, listing_id, current_user.id)
    listing = submit_listing_for_review(
        db=db,
        listing=listing,
        background_tasks=background_tasks,
    )

    return ListingSubmitResponse(
        message="Listing submitted for review. CV analysis started.",
        listing_id=listing.id,
        status=listing.status,
    )

def analyze_listing_image(
    db: Session,
    listing_id: UUID,
    image_id: UUID,
    current_user: User,
) -> ListingImageAnalyzeResponse:
    listing = get_listing_for_owner(db, listing_id, current_user.id)

    image = next((img for img in listing.images if img.id == image_id), None)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    if not image.image_url.startswith("/uploads/"):
        raise HTTPException(status_code=400, detail="Unsupported image URL")

    image_path = UPLOAD_DIR / image.image_url.replace("/uploads/", "", 1)

    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Image file not found")

    result = analyze_single_listing_image(
        image_path=image_path,
        primary_damage=listing.primary_damage,
        secondary_damage=listing.secondary_damage,
    )

    detections = []
    for det in result["detections"]:
        bbox = det["bbox"]
        detections.append(
            {
                "label": det["class"],
                "confidence": det["conf"],
                "source": det["damage_source"],
                "bbox": {
                    "x1": bbox[0],
                    "y1": bbox[1],
                    "x2": bbox[2],
                    "y2": bbox[3],
                },
            }
        )

    return ListingImageAnalyzeResponse(
        image_id=image.id,
        annotated_image_url=result["annotated_image_url"],
        primary_severity=result["primary_severity"],
        secondary_severity=result["secondary_severity"],
        detections=detections,
    )

def predict_listing_price(
    db: Session,
    listing_id: UUID,
    payload: ListingPricePredictRequest,
    current_user: User,
) -> ListingPricePredictResponse:
    listing = get_listing_for_owner(db, listing_id, current_user.id)

    if listing.status not in {ListingStatus.DRAFT, ListingStatus.REJECTED, ListingStatus.PENDING_REVIEW}:
        raise HTTPException(
            status_code=400,
            detail="Price prediction can only be run for draft, rejected, or pending_review listings",
        )

    if payload.use_cv:
        if not listing.images:
            raise HTTPException(
                status_code=400,
                detail="At least one image is required to run prediction with CV",
            )

        cv_result = run_listing_cv_analysis(db, listing)

        if cv_result.status != "done":
            return ListingPricePredictResponse(
                listing_id=listing.id,
                predicted_price=None,
                price_prediction_status=None,
                price_prediction_error=None,
                predicted_at=None,
                cv_status=cv_result.status,
                cv_error=cv_result.error,
                cv_processed_at=cv_result.processed_at,
                used_cv=True,
            )

        db.refresh(listing)

    price_result = run_price_prediction(db, listing)
    db.refresh(listing)

    return ListingPricePredictResponse(
        listing_id=listing.id,
        predicted_price=price_result.predicted_price,
        price_prediction_status=price_result.status,
        price_prediction_error=price_result.error,
        predicted_at=price_result.predicted_at,
        cv_status=listing.cv_result.status if listing.cv_result else None,
        cv_error=listing.cv_result.error if listing.cv_result else None,
        cv_processed_at=listing.cv_result.processed_at if listing.cv_result else None,
        used_cv=payload.use_cv,
    )
