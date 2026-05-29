from pathlib import Path
from decimal import Decimal
from datetime import datetime
import joblib
import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.models.listing import Listing
from backend.models.listing_price_prediction import ListingPricePrediction

MODEL_PATH = Path("ml/price_predictor.pkl")

_bundle = None

def get_price_bundle():
    global _bundle
    if _bundle is None:
        _bundle = joblib.load(MODEL_PATH)
    return _bundle

def _clean_text(x) -> str:
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return "UNKNOWN"
    x = str(x).strip().upper()
    return x if x else "UNKNOWN"

def _normalize_damage_severity(damage, severity) -> float:
    non_visual = {
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

    dmg = _clean_text(damage)
    sev = pd.to_numeric(pd.Series([severity]), errors="coerce").iloc[0]

    if pd.isna(sev):
        sev = 0.0

    if dmg in non_visual and sev <= 0:
        return 1.0

    return float(sev)

def get_or_create_price_prediction(db: Session, listing: Listing) -> ListingPricePrediction:
    if listing.price_prediction:
        return listing.price_prediction

    price_prediction = ListingPricePrediction(
        listing_id=listing.id,
    )
    db.add(price_prediction)
    db.commit()
    db.refresh(price_prediction)
    db.refresh(listing)
    return price_prediction

def _build_features_df(listing: Listing, bundle: dict) -> pd.DataFrame:
    row = {
        "make": listing.make,
        "model": listing.model,
        "fuel_type": listing.fuel_type,
        "transmission": listing.transmission,
        "drive_type": listing.drive_type,
        "primary_damage": listing.primary_damage,
        "secondary_damage": listing.secondary_damage,
        "mileage": listing.mileage,
        "engine_volume": listing.engine_volume,
        "cylinders": listing.cylinders,
        "year": listing.year,
        "primary_damage_severity": (
            listing.cv_result.primary_damage_severity if listing.cv_result else None
        ),
        "secondary_damage_severity": (
            listing.cv_result.secondary_damage_severity if listing.cv_result else None
        ),
        "color": listing.color,
        "currency": "USD",
    }

    df = pd.DataFrame([row])

    text_cols = [
        "make",
        "model",
        "primary_damage",
        "secondary_damage",
        "transmission",
        "fuel_type",
        "drive_type",
        "color",
    ]
    for col in text_cols:
        if col not in df.columns:
            df[col] = "UNKNOWN"
        df[col] = df[col].apply(_clean_text)

    for col in ["mileage", "year", "engine_volume", "cylinders"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    base = bundle["base_preprocess_bundle"]

    df["engine_volume"] = df["engine_volume"].fillna(base["engine_volume_median"])
    df["cylinders"] = df["cylinders"].fillna(base["cylinders_median"])

    df["primary_damage_severity"] = df.apply(
        lambda r: _normalize_damage_severity(r["primary_damage"], r["primary_damage_severity"]),
        axis=1,
    )
    df["secondary_damage_severity"] = df.apply(
        lambda r: _normalize_damage_severity(r["secondary_damage"], r["secondary_damage_severity"]),
        axis=1,
    )

    if df.loc[0, "fuel_type"] in {"ELECTRIC", "OTHER"}:
        df.loc[0, "engine_volume"] = 0
        df.loc[0, "cylinders"] = 0

    for col in ["make", "model", "color"]:
        keep_values = base["rare_maps"].get(col, set())
        df[col] = df[col].where(df[col].isin(keep_values), "OTHER")

    median_map = bundle["feature_stats_bundle"]["make_model_year_price_median_map"]
    global_median = bundle["feature_stats_bundle"]["make_model_year_price_median_global"]

    key = list(zip(df["make"], df["model"], df["year"]))
    df["make_model_year_price_median"] = pd.Series(key).map(median_map).fillna(global_median)

    return df[bundle["features"]].copy()

def predict_listing_price(listing: Listing) -> float:
    bundle = get_price_bundle()
    X = _build_features_df(listing, bundle)

    if "model" in bundle:
        pred = float(bundle["model"].predict(X)[0])
        return float(np.clip(pred, bundle["min_price"], bundle["max_price"]))

    linear_model = bundle.get("linear_model")
    log_model = bundle.get("log_model")
    mode = bundle.get("best_prediction_mode", "blend")

    if linear_model is None and log_model is None:
        raise ValueError("price_predictor.pkl does not contain an inference model")

    pred_linear = None
    pred_log = None

    if linear_model is not None:
        pred_linear = float(linear_model.predict(X)[0])
        pred_linear = float(np.clip(pred_linear, bundle["min_price"], bundle["max_price"]))

    if log_model is not None:
        pred_log = float(np.exp(log_model.predict(X)[0]))
        pred_log = float(np.clip(pred_log, bundle["min_price"], bundle["max_price"]))

    if mode == "linear":
        if pred_linear is None:
            raise ValueError("Bundle expects linear mode but linear_model is missing")
        return pred_linear

    if mode == "log":
        if pred_log is None:
            raise ValueError("Bundle expects log mode but log_model is missing")
        return pred_log

    if pred_linear is None or pred_log is None:
        raise ValueError("Bundle expects blend mode but one model is missing")

    pred = (
        bundle["linear_weight"] * pred_linear
        + bundle["log_weight"] * pred_log
    )
    return float(np.clip(pred, bundle["min_price"], bundle["max_price"]))

def run_price_prediction(db: Session, listing: Listing) -> ListingPricePrediction:
    price_prediction = get_or_create_price_prediction(db, listing)

    price_prediction.status = "processing"
    price_prediction.error = None
    db.add(price_prediction)
    db.commit()
    db.refresh(price_prediction)

    try:
        predicted_price = predict_listing_price(listing)

        price_prediction.predicted_price = Decimal(str(round(predicted_price, 2)))
        price_prediction.status = "done"
        price_prediction.error = None
        price_prediction.predicted_at = datetime.utcnow()

        db.add(price_prediction)
        db.commit()
        db.refresh(price_prediction)
        return price_prediction

    except Exception as exc:
        price_prediction.status = "failed"
        price_prediction.error = str(exc)
        price_prediction.predicted_at = datetime.utcnow()

        db.add(price_prediction)
        db.commit()
        db.refresh(price_prediction)
        return price_prediction

def run_price_prediction_by_id(listing_id):
    from backend.db.session import SessionLocal

    db = SessionLocal()
    try:
        stmt = (
            select(Listing)
            .options(
                selectinload(Listing.images),
                selectinload(Listing.cv_result),
                selectinload(Listing.price_prediction),
            )
            .where(Listing.id == listing_id)
        )
        listing = db.scalar(stmt)
        if not listing:
            return

        run_price_prediction(db, listing)
    finally:
        db.close()