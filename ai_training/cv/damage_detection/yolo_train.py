import time
from pathlib import Path
from ultralytics import YOLO

def _extract_ultralytics_metrics(metrics_obj):
    box = getattr(metrics_obj, "box", None)
    if box is not None:
        map50_95 = float(getattr(box, "map", 0.0))
        map50 = float(getattr(box, "map50", 0.0))
        precision = float(getattr(box, "mp", 0.0))
        recall = float(getattr(box, "mr", 0.0))
        return precision, recall, map50, map50_95

    rd = getattr(metrics_obj, "results_dict", {}) or {}
    map50 = float(rd.get("metrics/mAP50(B)", rd.get("mAP50", 0.0)) or 0.0)
    map50_95 = float(rd.get("metrics/mAP50-95(B)", rd.get("mAP50-95", 0.0)) or 0.0)
    precision = float(rd.get("metrics/precision(B)", rd.get("precision", 0.0)) or 0.0)
    recall = float(rd.get("metrics/recall(B)", rd.get("recall", 0.0)) or 0.0)
    return precision, recall, map50, map50_95

def yolo_train(
    data_yaml: Path,
    runs_dir: Path,
    weights: str,
    run_name: str,
    imgsz: int = 640,
    batch: int = 8,
    epochs: int = 50,
    workers: int = 0,
    device: int = 0,
):
    runs_dir.mkdir(parents=True, exist_ok=True)

    model = YOLO(weights)

    t0 = time.time()
    model.train(
        data=str(data_yaml),
        imgsz=imgsz,
        batch=batch,
        epochs=epochs,
        workers=workers,
        device=device,
        project=str(runs_dir),
        name=run_name,
        cache=False,
        amp=True,
        patience=20,
        verbose=True,
    )
    train_seconds = time.time() - t0

    best_path = runs_dir / run_name / "weights" / "best.pt"
    best_model = YOLO(str(best_path))

    # VALIDATION
    t1 = time.time()
    val_metrics = best_model.val(
        data=str(data_yaml),
        imgsz=imgsz,
        device=device,
        workers=0,
        split="val",
    )
    val_seconds = time.time() - t1

    # TEST
    t2 = time.time()
    test_metrics = best_model.val(
        data=str(data_yaml),
        imgsz=imgsz,
        device=device,
        workers=0,
        split="test",
    )
    test_seconds = time.time() - t2

    val_p, val_r, val_map50, val_map50_95 = _extract_ultralytics_metrics(val_metrics)
    test_p, test_r, test_map50, test_map50_95 = _extract_ultralytics_metrics(test_metrics)

    return {
        "family": "YOLO",
        "run_name": run_name,
        "weights": weights,
        "imgsz": imgsz,
        "batch": batch,
        "epochs": epochs,
        "workers": workers,
        "train_seconds": round(train_seconds, 2),
        "val_seconds": round(val_seconds, 2),
        "test_seconds": round(test_seconds, 2),

        "val_precision": val_p,
        "val_recall": val_r,
        "val_mAP50": val_map50,
        "val_mAP50_95": val_map50_95,

        "test_precision": test_p,
        "test_recall": test_r,
        "test_mAP50": test_map50,
        "test_mAP50_95": test_map50_95,

        "artifact": str(best_path),
    }
