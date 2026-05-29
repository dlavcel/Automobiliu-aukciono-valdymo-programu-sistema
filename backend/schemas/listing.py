from datetime import datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from backend.enums.auction_status import AuctionStatus
from backend.enums.damage_type import DamageType
from backend.enums.listing_status import ListingStatus
from backend.enums.auction_type import AuctionType
from backend.enums.sale_result_status import SaleResultStatus
from backend.enums.sale_type import SaleType
from backend.enums.vehicle import DriveType, FuelType, Transmission

class ListingImageCreate(BaseModel):
    image_url: str = Field(..., min_length=5)
    sort_order: int = 0

class ListingImageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    image_url: str
    sort_order: int
    created_at: datetime

class ListingCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    make: str = Field(..., min_length=1, max_length=100)
    model: str = Field(..., min_length=1, max_length=100)
    year: int

    auction_type: AuctionType
    sale_type: SaleType
    reserve_price: Decimal | None = Field(default=None, gt=0)

    vin: str | None = Field(default=None, max_length=50)
    mileage: int | None = None
    fuel_type: FuelType | None = None
    engine_volume: float | None = None
    cylinders: int | None = None
    drive_type: DriveType | None = None
    transmission: Transmission | None = None
    body_type: str | None = Field(default=None, max_length=50)
    color: str | None = Field(default=None, max_length=50)
    primary_damage: DamageType | None = None
    secondary_damage: DamageType | None = None
    description: str | None = None
    location: str | None = Field(default=None, max_length=255)

    @field_validator("make", "model")
    @classmethod
    def uppercase_fields(cls, value: str | None):
        if value:
            return value.upper()
        return value

    @field_validator("year")
    @classmethod
    def validate_year(cls, value: int) -> int:
        if value < 1900 or value > 2026:
            raise ValueError("year must be between 1900 and 2026")
        return value

    @field_validator("mileage")
    @classmethod
    def validate_mileage(cls, value: int | None) -> int | None:
        if value is not None and value < 0:
            raise ValueError("mileage must be non-negative")
        return value

    @model_validator(mode="after")
    def validate_sale_config(self):
        if self.sale_type == SaleType.RESERVE_PRICE:
            if self.reserve_price is None:
                raise ValueError("reserve_price is required when sale_type is reserve_price")
        else:
            if self.reserve_price is not None:
                raise ValueError("reserve_price can be set only when sale_type is reserve_price")

        return self

class ListingUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=255)
    make: str | None = Field(default=None, min_length=1, max_length=100)
    model: str | None = Field(default=None, min_length=1, max_length=100)
    year: int | None = None

    auction_type: AuctionType | None = None
    sale_type: SaleType | None = None
    reserve_price: Decimal | None = Field(default=None, gt=0)

    vin: str | None = Field(default=None, max_length=50)
    mileage: int | None = None
    fuel_type: FuelType | None = None
    engine_volume: float | None = None
    cylinders: int | None = None
    drive_type: DriveType | None = None
    transmission: Transmission | None = None
    body_type: str | None = Field(default=None, max_length=50)
    color: str | None = Field(default=None, max_length=50)
    primary_damage: DamageType | None = None
    secondary_damage: DamageType | None = None
    description: str | None = None
    location: str | None = Field(default=None, max_length=255)

    @field_validator("make", "model")
    @classmethod
    def uppercase_fields(cls, value: str | None):
        if value:
            return value.upper()
        return value

    @model_validator(mode="after")
    def validate_sale_config(self):
        if self.sale_type == SaleType.RESERVE_PRICE and self.reserve_price is None:
            raise ValueError("reserve_price is required when sale_type is reserve_price")
        return self

class ListingAuctionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    current_price: Decimal | None = None
    starts_at: datetime
    ends_at: datetime
    status: AuctionStatus
    sale_result_status: SaleResultStatus

class ListingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    owner_user_id: UUID

    title: str
    make: str
    model: str
    year: int

    auction_type: AuctionType
    sale_type: SaleType
    reserve_price: Decimal | None = None

    vin: str | None = Field(default=None, max_length=50)
    mileage: int | None = None

    fuel_type: FuelType | None = None
    engine_volume: float | None = None
    cylinders: int | None = None
    drive_type: DriveType | None = None
    transmission: Transmission | None = None
    body_type: str | None = Field(default=None, max_length=50)
    color: str | None = Field(default=None, max_length=50)

    primary_damage: DamageType | None = None
    secondary_damage: DamageType | None = None
    description: str | None = None
    location: str | None = Field(default=None, max_length=255)

    primary_damage_severity: Decimal | None = None
    secondary_damage_severity: Decimal | None = None

    predicted_price: Decimal | None = None

    status: ListingStatus
    rejection_reason: str | None = None

    submitted_at: datetime | None = None
    reviewed_at: datetime | None = None
    reviewed_by: UUID | None = None

    created_at: datetime
    updated_at: datetime

    images: list[ListingImageRead] = []
    auction: ListingAuctionRead | None = None

class ListingSubmitResponse(BaseModel):
    message: str
    listing_id: UUID
    status: ListingStatus

class ListingRejectRequest(BaseModel):
    reason: str = Field(..., min_length=3, max_length=2000)

class ListingPricePredictRequest(BaseModel):
    use_cv: bool = True

class ListingPricePredictResponse(BaseModel):
    listing_id: UUID
    predicted_price: Decimal | None = None

    price_prediction_status: str | None = None
    price_prediction_error: str | None = None
    predicted_at: datetime | None = None

    cv_status: str | None = None
    cv_error: str | None = None
    cv_processed_at: datetime | None = None

    used_cv: bool

class DetectionBBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float

class ListingImageDetectionRead(BaseModel):
    label: str
    confidence: float
    source: str
    bbox: DetectionBBox

class ListingImageAnalyzeResponse(BaseModel):
    image_id: UUID
    annotated_image_url: str
    primary_severity: Decimal | None = None
    secondary_severity: Decimal | None = None
    detections: list[ListingImageDetectionRead] = []