import cv2
from pathlib import Path
from ultralytics import YOLO
from uuid import uuid4

from backend.cv.severity_estimation import score_view

BASE_DIR = Path(__file__).resolve().parent

model_primary = YOLO(BASE_DIR / "yolov8m30.pt")
model_secondary = YOLO(BASE_DIR / "yolov8m120.pt")

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
    "TRANSMISSION DAMAGE",
    "UNKNOWN",
    "WATER/FLOOD",
    "REPLACED VIN",
    "UNDERCARRIAGE",
}

def convert_to_dets(result):
    dets = []

    if not result or result[0].boxes is None:
        return dets

    boxes = result[0].boxes
    names = result[0].names

    for b, c, cls in zip(boxes.xyxy, boxes.conf, boxes.cls):
        class_id = int(cls)

        if isinstance(names, dict):
            class_name = names.get(class_id, str(class_id))
        elif isinstance(names, list) and 0 <= class_id < len(names):
            class_name = names[class_id]
        else:
            class_name = str(class_id)

        dets.append(
            {
                "bbox": b.tolist(),
                "conf": float(c),
                "class": class_name,
            }
        )

    return dets

def _damage_value(damage):
    if damage is None:
        return None
    return getattr(damage, "value", damage)

def _is_visual_damage(damage) -> bool:
    damage_value = _damage_value(damage)
    return damage_value is not None and damage_value not in NON_VISUAL

def evaluate_listing_images(
    image_paths: list[Path],
    primary_damage,
    secondary_damage,
):
    view_scores_primary = {}
    view_scores_secondary = {}

    primary_is_visual = _is_visual_damage(primary_damage)
    secondary_is_visual = _is_visual_damage(secondary_damage)

    for i, path in enumerate(image_paths, start=1):
        img = cv2.imread(str(path))
        if img is None:
            continue

        H, W = img.shape[:2]

        if primary_is_visual:
            res_p = model_primary(str(path))
            dets_p = convert_to_dets(res_p)
            view_scores_primary[i] = score_view(dets_p, W, H)["severity"]

        if secondary_is_visual:
            res_s = model_secondary(str(path))
            dets_s = convert_to_dets(res_s)
            view_scores_secondary[i] = score_view(dets_s, W, H)["severity"]

    primary = None
    secondary = None

    if primary_is_visual:
        primary = max(
            [v for v in view_scores_primary.values() if v is not None],
            default=None,
        )

    if secondary_is_visual:
        secondary = max(
            [v for v in view_scores_secondary.values() if v is not None],
            default=None,
        )

    primary = -1 if primary is None else primary
    secondary = -1 if secondary is None else secondary

    return primary, secondary

ANNOTATED_DIR = Path("uploads/annotated")
ANNOTATED_DIR.mkdir(parents=True, exist_ok=True)

def draw_detections(image, detections, color=(0, 255, 0)):
    for det in detections:
        x1, y1, x2, y2 = [int(v) for v in det["bbox"]]
        label = det["class"]
        conf = det["conf"]

        text = f"{label} {conf:.2f}"

        cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
        cv2.putText(
            image,
            text,
            (x1, max(y1 - 8, 20)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            color,
            2,
        )

    return image

def analyze_single_listing_image(
    image_path: Path,
    primary_damage,
    secondary_damage,
):

    dets_p = []
    dets_s = []

    img = cv2.imread(str(image_path))
    if img is None:
        raise ValueError("Image could not be read")

    H, W = img.shape[:2]

    primary_is_visual = _is_visual_damage(primary_damage)
    secondary_is_visual = _is_visual_damage(secondary_damage)

    all_detections = []
    primary_severity = None
    secondary_severity = None

    print("PRIMARY DAMAGE:", primary_damage)
    print("SECONDARY DAMAGE:", secondary_damage)
    print("PRIMARY IS VISUAL:", primary_is_visual)
    print("SECONDARY IS VISUAL:", secondary_is_visual)

    if primary_is_visual:
        res_p = model_primary(str(image_path))
        dets_p = convert_to_dets(res_p)

        primary_score = score_view(dets_p, W, H)
        primary_severity = primary_score["severity"]

        for det in dets_p:
            all_detections.append({
                "damage_source": "primary",
                "bbox": det["bbox"],
                "conf": det["conf"],
                "class": det["class"],
            })

    if secondary_is_visual:
        res_s = model_secondary(str(image_path))
        dets_s = convert_to_dets(res_s)

        secondary_score = score_view(dets_s, W, H)
        secondary_severity = secondary_score["severity"]

        for det in dets_s:
            all_detections.append({
                "damage_source": "secondary",
                "bbox": det["bbox"],
                "conf": det["conf"],
                "class": det["class"],
            })

    if primary_is_visual and primary_severity is None:
        primary_severity = -1

    if secondary_is_visual and secondary_severity is None:
        secondary_severity = -1

    print("PRIMARY DETECTIONS:", dets_p)
    print("SECONDARY DETECTIONS:", dets_s)
    annotated = img.copy()
    draw_detections(annotated, all_detections)

    filename = f"{uuid4()}.jpg"
    output_path = ANNOTATED_DIR / filename
    cv2.imwrite(str(output_path), annotated)

    print("ALL DETECTIONS:", all_detections)
    print("PRIMARY SEVERITY:", primary_severity)
    print("SECONDARY SEVERITY:", secondary_severity)
    return {
        "annotated_image_url": f"/uploads/annotated/{filename}",
        "primary_severity": primary_severity,
        "secondary_severity": secondary_severity,
        "detections": all_detections,
    }