import argparse
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import cv2
import numpy as np
import pandas as pd
import torch
from ultralytics import YOLO
from torchvision.ops import nms

from backend.cv.severity_estimation import score_view

NON_VISUAL = {
    "BIOHAZARD/CHEMICAL",
    "DAMAGE HISTORY",
    "ELECTRICAL",
    "ENGINE DAMAGE",
    "FRAME DAMAGE",
    "MECHANICAL",
    "MISSING/ALTERED VIN",
    "NORMAL WEAR",
    "REPOSSESSION",
    "SUSPENSION",
    "THEFT",
    "TRANSMISSION DAMAGE",
    "UNKNOWN",
    "WATER/FLOOD",
    "UNDERCARRIAGE",
    "REPLACED VIN",
}


def normalize_damage_label(dmg: Optional[str]) -> str:
    if dmg is None or pd.isna(dmg):
        return "NONE"

    d = str(dmg).strip().upper()
    if d in {"", "NONE", "N/A", "NA", "NULL", "NAN"}:
        return "NONE"
    return d


def is_visual_damage(dmg: Optional[str]) -> bool:
    d = normalize_damage_label(dmg)
    if d == "NONE":
        return False
    return d not in NON_VISUAL


def visual_or_none(dmg: Optional[str]) -> Optional[str]:
    return dmg if is_visual_damage(dmg) else None


def damage_to_key(dmg: Optional[str]) -> str:
    d = normalize_damage_label(dmg)
    if d == "NONE":
        return "NONE"

    if d == "FRONT END":
        return "FRONT_END"
    if d == "REAR END":
        return "REAR_END"
    if d == "SIDE":
        return "SIDE"
    if d == "FRONT & REAR":
        return "FRONT_REAR"
    if d == "ALL OVER":
        return "ALL_OVER"
    if d == "TOP/ROOF":
        return "TOP_ROOF"
    if d == "UNDERCARRIAGE":
        return "UNDERCARRIAGE"
    if d == "MINOR DENT/SCRATCHES":
        return "MINOR"

    if d in {"HAIL", "STORM DAMAGE", "ROLLOVER", "STRIP", "VANDALISM", "BURN", "PARTIAL REPAIR"}:
        return "ALL_OVER"

    if d in {"BURN - ENGINE", "BURN - INTERIOR"}:
        return "ALL_OVER"

    return "OTHER"


def select_indices_for_damage_key(damage_key: str, n_imgs: int) -> List[int]:
    if n_imgs == 6:
        if damage_key == "FRONT_END":
            return [1, 4, 5]
        if damage_key == "REAR_END":
            return [2, 3, 6]
        if damage_key == "SIDE":
            return [1, 2, 3, 4]
        if damage_key in {"FRONT_REAR", "ALL_OVER", "MINOR", "OTHER", "TOP_ROOF", "UNDERCARRIAGE"}:
            return [1, 2, 3, 4, 5, 6]
        return [1, 2, 3, 4, 5, 6]

    if n_imgs == 4:
        if damage_key == "FRONT_END":
            return [1, 2]
        if damage_key == "REAR_END":
            return [3, 4]
        if damage_key == "SIDE":
            return [1, 2, 3, 4]
        if damage_key in {"FRONT_REAR", "ALL_OVER", "MINOR", "OTHER", "TOP_ROOF", "UNDERCARRIAGE"}:
            return [1, 2, 3, 4]
        return [1, 2, 3, 4]

    return list(range(1, n_imgs + 1))


def select_primary_secondary_indices(
    primary_key: str,
    secondary_key: str,
    n_imgs: int,
    mode: str = "baseline",
) -> Tuple[List[int], List[int]]:
    if mode not in {"baseline", "disjoint"}:
        raise ValueError("mode must be 'baseline' or 'disjoint'")

    p = primary_key
    s = secondary_key

    if mode == "disjoint":
        if {p, s} == {"FRONT_END", "SIDE"}:
            if n_imgs == 6:
                p_idx = [1, 4, 5] if p == "FRONT_END" else [2, 3]
                s_idx = [2, 3] if s == "SIDE" else [1, 4, 5]
                return p_idx, s_idx
            if n_imgs == 4:
                p_idx = [1, 2] if p == "FRONT_END" else [3, 4]
                s_idx = [3, 4] if s == "SIDE" else [1, 2]
                return p_idx, s_idx

        if {p, s} == {"REAR_END", "SIDE"}:
            if n_imgs == 6:
                p_idx = [2, 3, 6] if p == "REAR_END" else [1, 4]
                s_idx = [1, 4] if s == "SIDE" else [2, 3, 6]
                return p_idx, s_idx
            if n_imgs == 4:
                p_idx = [3, 4] if p == "REAR_END" else [1, 2]
                s_idx = [1, 2] if s == "SIDE" else [3, 4]
                return p_idx, s_idx

    p_idx = select_indices_for_damage_key(p, n_imgs) if p != "NONE" else []
    s_idx = select_indices_for_damage_key(s, n_imgs) if s != "NONE" else []
    return p_idx, s_idx


def max_severity_for_indices(view_sev: Dict[int, Optional[float]], indices: List[int]) -> Optional[float]:
    vals = [view_sev.get(i) for i in indices]
    vals = [v for v in vals if v is not None]
    return max(vals) if vals else None


def tile_windows(W, H, grid=1, overlap=0.2):
    assert 0 <= overlap < 0.5
    tile_w = int(np.ceil(W / grid))
    tile_h = int(np.ceil(H / grid))

    stride_w = int(tile_w * (1 - overlap))
    stride_h = int(tile_h * (1 - overlap))
    stride_w = max(1, stride_w)
    stride_h = max(1, stride_h)

    tiles = []
    ys = list(range(0, max(1, H - tile_h + 1), stride_h))
    xs = list(range(0, max(1, W - tile_w + 1), stride_w))

    if len(xs) == 0 or xs[-1] != W - tile_w:
        xs.append(max(0, W - tile_w))
    if len(ys) == 0 or ys[-1] != H - tile_h:
        ys.append(max(0, H - tile_h))

    for y in ys:
        for x in xs:
            x1, y1 = x, y
            x2, y2 = min(W, x + tile_w), min(H, y + tile_h)
            tiles.append((x1, y1, x2, y2))
    return tiles


def class_aware_nms(boxes_xyxy, scores, class_ids, iou_thres=0.6):
    keep_all = []
    unique_classes = torch.unique(class_ids)
    for c in unique_classes:
        idx = torch.where(class_ids == c)[0]
        if idx.numel() == 0:
            continue
        keep = nms(boxes_xyxy[idx], scores[idx], iou_thres)
        keep_all.append(idx[keep])
    if not keep_all:
        return torch.empty((0,), dtype=torch.long, device=boxes_xyxy.device)
    return torch.cat(keep_all, dim=0)


def yolo_tiled_predict(
    model: YOLO,
    image_bgr: np.ndarray,
    imgsz=1024,
    conf=0.2,
    iou_tile=0.6,
    iou_merge=0.4,
    grid=1,
    overlap=0.2,
    device=None,
):
    H, W = image_bgr.shape[:2]
    tiles = tile_windows(W, H, grid=1, overlap=overlap)

    all_boxes = []
    all_scores = []
    all_classes = []

    with torch.inference_mode():
        for (x1, y1, x2, y2) in tiles:
            tile = image_bgr[y1:y2, x1:x2]

            results = model.predict(
                source=tile,
                imgsz=imgsz,
                conf=conf,
                iou=iou_tile,
                device=device,
                verbose=False,
            )

            r = results[0]
            if r.boxes is None or len(r.boxes) == 0:
                continue

            b = r.boxes.xyxy
            s = r.boxes.conf
            c = r.boxes.cls.to(torch.int64)

            if device is not None and b.device.type == "cpu":
                b = b.to("cuda")
                s = s.to("cuda")
                c = c.to("cuda")

            b = b.clone()
            b[:, [0, 2]] += float(x1)
            b[:, [1, 3]] += float(y1)

            all_boxes.append(b)
            all_scores.append(s)
            all_classes.append(c)

        if not all_boxes:
            return (
                np.zeros((0, 4), dtype=np.float32),
                np.zeros((0,), dtype=np.float32),
                np.zeros((0,), dtype=np.int32),
            )

        boxes_t = torch.cat(all_boxes, dim=0)
        scores_t = torch.cat(all_scores, dim=0)
        classes_t = torch.cat(all_classes, dim=0)

        keep = class_aware_nms(boxes_t, scores_t, classes_t, iou_thres=iou_merge)

        boxes = boxes_t[keep].detach().cpu().numpy().astype(np.float32)
        scores = scores_t[keep].detach().cpu().numpy().astype(np.float32)
        classes = classes_t[keep].detach().cpu().numpy().astype(np.int32)

        return boxes, scores, classes


def to_detection_dicts(boxes, scores, classes, names_dict=None):
    dets = []
    for b, sc, cl in zip(boxes, scores, classes):
        cls_name = names_dict[int(cl)] if names_dict is not None else str(int(cl))
        dets.append({
            "class": cls_name,
            "conf": float(sc),
            "bbox": [float(b[0]), float(b[1]), float(b[2]), float(b[3])],
        })
    return dets

def natural_sort_key(name: str):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", name)]

def list_images(folder: Path) -> List[Path]:
    exts = (".jpg", ".jpeg", ".png")
    imgs = [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in exts]
    return sorted(imgs, key=lambda p: natural_sort_key(p.name))

def infer_n_imgs(image_paths: List[Path]) -> int:
    n = len(image_paths)
    if n in (4, 6):
        return n
    if n > 6:
        return 6
    return n

def normalize_vin(v) -> Optional[str]:
    if v is None or pd.isna(v):
        return None
    s = str(v).strip().upper()
    return s if s else None


def get_vin_from_row(row: pd.Series) -> Optional[str]:
    for col in ["vin", "VIN"]:
        if col in row.index:
            vin = normalize_vin(row[col])
            if vin:
                return vin
    return None


def build_vin_folder_index(cars_root: Path) -> Dict[str, List[str]]:
    vin_to_folders: Dict[str, List[str]] = {}

    for folder in os.listdir(cars_root):
        folder_path = cars_root / folder
        if not folder_path.is_dir():
            continue

        folder_name = folder.strip()
        if not folder_name:
            continue

        if "_" in folder_name:
            vin = folder_name.split("_", 1)[1].strip().upper()
        else:
            vin = folder_name.upper()

        if not vin:
            continue

        vin_to_folders.setdefault(vin, []).append(folder_name)

    for vin in vin_to_folders:
        vin_to_folders[vin] = sorted(vin_to_folders[vin], key=natural_sort_key)

    return vin_to_folders


def find_folder_by_vin(vin: Optional[str], vin_to_folders: Dict[str, List[str]]) -> Optional[str]:
    if vin is None:
        return None

    matches = vin_to_folders.get(vin, [])
    if not matches:
        return None

    exact_suffix_matches = [f for f in matches if f.upper().endswith(f"_{vin}")]
    if exact_suffix_matches:
        return sorted(exact_suffix_matches, key=natural_sort_key)[0]

    return matches[0]


def score_views_for_car(
    model: YOLO,
    car_dir: Path,
    device=None,
    imgsz=1024,
    conf=0.2,
    iou_tile=0.6,
    iou_merge=0.4,
    overlap=0.2,
) -> Tuple[Dict[int, Optional[float]], int]:
    image_paths = list_images(car_dir)
    if not image_paths:
        return {}, 0

    n_in_folder = len(image_paths)
    n_imgs = infer_n_imgs(image_paths)

    if n_imgs not in (4, 6):
        return {}, n_in_folder

    image_paths = image_paths[:n_imgs]

    names = model.names if hasattr(model, "names") else None
    names_dict = names if isinstance(names, dict) else {i: n for i, n in enumerate(names)} if names else None

    view_sev: Dict[int, Optional[float]] = {}
    for idx, img_path in enumerate(image_paths, start=1):
        img = cv2.imread(str(img_path))
        if img is None:
            view_sev[idx] = None
            continue

        H, W = img.shape[:2]
        boxes, scores, classes = yolo_tiled_predict(
            model=model,
            image_bgr=img,
            imgsz=imgsz,
            conf=conf,
            iou_tile=iou_tile,
            iou_merge=iou_merge,
            overlap=overlap,
            device=device,
        )
        dets = to_detection_dicts(boxes, scores, classes, names_dict=names_dict)

        vr = score_view(dets, img_w=W, img_h=H)
        view_sev[idx] = vr.get("severity", None)

    return view_sev, n_imgs

def compute_primary_secondary(
    view_sev: Dict[int, Optional[float]],
    n_imgs: int,
    primary_damage: Optional[str],
    secondary_damage: Optional[str],
    mode: str = "baseline",
) -> Tuple[Optional[float], Optional[float]]:
    p_key = damage_to_key(primary_damage)
    s_key = damage_to_key(secondary_damage)

    p_idx, s_idx = select_primary_secondary_indices(p_key, s_key, n_imgs, mode=mode)

    primary_sev = max_severity_for_indices(view_sev, p_idx) if (primary_damage is not None and p_idx) else None
    secondary_sev = max_severity_for_indices(view_sev, s_idx) if (secondary_damage is not None and s_idx) else None

    return primary_sev, secondary_sev

def detect_human_severity_column(df: pd.DataFrame) -> str:
    candidates = [
        "severity",
        "human_severity",
        "human_estimation",
        "damage_severity",
        "estimated_severity",
    ]
    lower_map = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in lower_map:
            return lower_map[cand.lower()]

    raise ValueError(
        "human_csv must contain one of columns: "
        "severity, human_severity, human_estimation, damage_severity, estimated_severity"
    )

def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--cars_root", type=str, default="F:/cars")
    parser.add_argument("--human_csv", type=str, default="human_estimation.csv")
    parser.add_argument("--cars_csv", type=str, default="../cars.csv")

    parser.add_argument("--yolov8m30_weights", type=str, default="yolov8m30.pt")
    parser.add_argument("--yolov8m120_weights", type=str, default="yolov8m120.pt")

    parser.add_argument("--out_csv", type=str, default="../no_grid/l2_nogrid_640.csv")
    parser.add_argument("--mode", type=str, default="baseline", choices=["baseline", "disjoint"])

    parser.add_argument("--yolov8m30_imgsz", type=int, default=640)
    parser.add_argument("--yolov8m30_conf", type=float, default=0.5)
    parser.add_argument("--yolov8m30_iou_tile", type=float, default=0.45)
    parser.add_argument("--yolov8m30_iou_merge", type=float, default=0.25)
    parser.add_argument("--yolov8m30_overlap", type=float, default=0.1)

    parser.add_argument("--yolov8m120_imgsz", type=int, default=640)
    parser.add_argument("--yolov8m120_conf", type=float, default=0.5)
    parser.add_argument("--yolov8m120_iou_tile", type=float, default=0.45)
    parser.add_argument("--yolov8m120_iou_merge", type=float, default=0.25)
    parser.add_argument("--yolov8m120_overlap", type=float, default=0.1)

    return parser.parse_args()


def extract_vin_from_folder(folder: str) -> Optional[str]:
    if not isinstance(folder, str):
        return None

    parts = folder.split("_", 1)
    if len(parts) == 2:
        return parts[1].strip().upper()

    return folder.strip().upper()


def main():
    args = parse_args()

    cars_root = Path(args.cars_root)
    human_csv = Path(args.human_csv)
    cars_csv = Path(args.cars_csv)
    out_csv = Path(args.out_csv)

    human_df = pd.read_csv(human_csv)
    cars_df = pd.read_csv(cars_csv)

    # --- проверки ---
    if "folder" not in human_df.columns:
        raise ValueError("human_csv must contain column 'folder'")

    if "vin" not in cars_df.columns:
        raise ValueError("cars_csv must contain column 'vin'")

    if {"damage_primary", "damage_secondary"}.issubset(cars_df.columns):
        primary_col = "damage_primary"
        secondary_col = "damage_secondary"
    elif {"primary_damage", "secondary_damage"}.issubset(cars_df.columns):
        primary_col = "primary_damage"
        secondary_col = "secondary_damage"
    else:
        raise ValueError("cars_csv must contain damage columns")

    cars_df["vin"] = cars_df["vin"].astype(str).str.strip().str.upper()

    cars_df = cars_df.drop_duplicates("vin", keep="first")
    cars_by_vin = cars_df.set_index("vin")

    device = 0 if torch.cuda.is_available() else None

    yolov8m30 = YOLO(args.yolov8m30_weights)
    yolov8m120 = YOLO(args.yolov8m120_weights)

    rows = []

    for _, row in human_df.iterrows():
        folder = str(row["folder"]).strip()
        vin = extract_vin_from_folder(folder)

        car_dir = cars_root / folder

        primary_damage_raw = None
        secondary_damage_raw = None

        if vin and vin in cars_by_vin.index:
            car_meta = cars_by_vin.loc[vin]
            primary_damage_raw = car_meta.get(primary_col, None)
            secondary_damage_raw = car_meta.get(secondary_col, None)
        else:
            print(f"[MISS VIN] folder={folder}, vin={vin}")

        primary_damage = visual_or_none(primary_damage_raw)
        secondary_damage = visual_or_none(secondary_damage_raw)

        y30_p = y30_s = y120_p = y120_s = None

        if car_dir.exists():
            image_paths = list_images(car_dir)
            n_imgs = infer_n_imgs(image_paths)

            if n_imgs in (4, 6):
                view_30, _ = score_views_for_car(
                    model=yolov8m30,
                    car_dir=car_dir,
                    device=device,
                    imgsz=args.yolov8m30_imgsz,
                    conf=args.yolov8m30_conf,
                    iou_tile=args.yolov8m30_iou_tile,
                    iou_merge=args.yolov8m30_iou_merge,
                    overlap=args.yolov8m30_overlap,
                )

                y30_p, y30_s = compute_primary_secondary(
                    view_sev=view_30,
                    n_imgs=n_imgs,
                    primary_damage=primary_damage,
                    secondary_damage=secondary_damage,
                    mode=args.mode,
                )

                view_120, _ = score_views_for_car(
                    model=yolov8m120,
                    car_dir=car_dir,
                    device=device,
                    imgsz=args.yolov8m120_imgsz,
                    conf=args.yolov8m120_conf,
                    iou_tile=args.yolov8m120_iou_tile,
                    iou_merge=args.yolov8m120_iou_merge,
                    overlap=args.yolov8m120_overlap,
                )

                y120_p, y120_s = compute_primary_secondary(
                    view_sev=view_120,
                    n_imgs=n_imgs,
                    primary_damage=primary_damage,
                    secondary_damage=secondary_damage,
                    mode=args.mode,
                )
        else:
            print(f"[NO FOLDER] {folder}")

        rows.append({
            "folder": folder,
            "vin": vin,
            "primary_damage": primary_damage_raw,
            "secondary_damage": secondary_damage_raw,
            "yolov8m30_primary": y30_p,
            "yolov8m30_secondary": y30_s,
            "yolov8m120_primary": y120_p,
            "yolov8m120_secondary": y120_s,
        })

        print(
            f"{folder}: "
            f"y30=({y30_p}, {y30_s}), "
            f"y120=({y120_p}, {y120_s})"
        )

    df = pd.DataFrame(rows)
    df.to_csv(out_csv, index=False)

    print("\nSaved:", out_csv)

if __name__ == "__main__":
    main()