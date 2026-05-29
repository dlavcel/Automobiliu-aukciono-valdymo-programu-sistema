from datetime import datetime
from pathlib import Path
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.db.session import SessionLocal
from backend.cv.pipeline import evaluate_listing_images
from backend.models.listing import Listing
from backend.models.listing_cv_result import ListingCVResult
from backend.services.price_prediction_service import run_price_prediction_by_id

UPLOAD_DIR = Path("uploads")

NON_VISUAL = {
    "BIOHAZARD",
    "DAMAGE HISTORY",
    "ELECTRICAL",
    "ENGINE DAMAGE",
    "FRAME DAMAGE",
    "MECHANICAL",
    "MISSING/ALTERED VIN",
    "NORMAL WEAR & TEAR",
    "CASH FOR CLUNKERS",
    "REPOSSESSION",
    "SUSPENSION",
    "THEFT",
    "MINOR",
    "TRANSMISSION DAMAGE",
    "UNKNOWN",
    "WATER/FLOOD",
    "REPLACED VIN",
    "UNDERCARRIAGE",
}


def is_visual_damage(dmg: str | None) -> bool:
    if not dmg:
        return False
    return str(dmg).strip().upper() not in NON_VISUAL


def get_or_create_cv_result(db: Session, listing: Listing) -> ListingCVResult:
    if listing.cv_result:
        return listing.cv_result

    cv_result = ListingCVResult(
        listing_id=listing.id,
    )
    db.add(cv_result)
    db.commit()
    db.refresh(cv_result)
    db.refresh(listing)
    return cv_result


def run_listing_cv_analysis_by_id(listing_id: UUID) -> None:
    db = SessionLocal()
    try:
        stmt = (
            select(Listing)
            .options(
                selectinload(Listing.images),
                selectinload(Listing.cv_result),
            )
            .where(Listing.id == listing_id)
        )
        listing = db.scalar(stmt)
        if not listing:
            return

        cv_result = run_listing_cv_analysis(db, listing)

        if cv_result.status == "done":
            run_price_prediction_by_id(listing.id)
    finally:
        db.close()


def run_listing_cv_analysis(db: Session, listing: Listing) -> ListingCVResult:
    cv_result = get_or_create_cv_result(db, listing)

    cv_result.status = "processing"
    cv_result.error = None
    db.add(cv_result)
    db.commit()
    db.refresh(cv_result)

    try:
        image_paths = get_listing_image_paths(listing)

        if not image_paths:
            raise ValueError("Listing has no images")

        primary_severity = None
        secondary_severity = None

        need_primary = is_visual_damage(listing.primary_damage)
        need_secondary = is_visual_damage(listing.secondary_damage)

        if need_primary or need_secondary:
            primary_severity, secondary_severity = evaluate_listing_images(
                image_paths=image_paths,
                primary_damage=listing.primary_damage if need_primary else None,
                secondary_damage=listing.secondary_damage if need_secondary else None,
            )

        cv_result.primary_damage_severity = primary_severity
        cv_result.secondary_damage_severity = secondary_severity
        cv_result.status = "done"
        cv_result.error = None
        cv_result.processed_at = datetime.utcnow()

        db.add(cv_result)
        db.commit()
        db.refresh(cv_result)
        return cv_result

    except Exception as exc:
        cv_result.status = "failed"
        cv_result.error = str(exc)
        cv_result.processed_at = datetime.utcnow()

        db.add(cv_result)
        db.commit()
        db.refresh(cv_result)
        return cv_result


def get_listing_image_paths(listing: Listing) -> list[Path]:
    sorted_images = sorted(listing.images, key=lambda img: img.sort_order)
    paths = []

    for img in sorted_images:
        if not img.image_url.startswith("/uploads/"):
            raise ValueError(f"Unsupported image_url format: {img.image_url}")

        path = Path("uploads") / img.image_url.replace("/uploads/", "", 1)
        if not path.exists():
            raise ValueError(f"Image file not found: {path}")

        paths.append(path)

    return paths