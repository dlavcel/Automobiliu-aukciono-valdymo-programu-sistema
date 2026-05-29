import csv
import gc
from pathlib import Path
import torch

from yolo_train import yolo_train

ROOT = Path(__file__).parent
RUNS_DIR = ROOT / "runs"
RESULTS_CSV = ROOT / "results_all.csv"
DATA_YAML = ROOT / "dataset" / "data.yaml"

def append_row(row: dict):
    file_exists = RESULTS_CSV.exists()
    with open(RESULTS_CSV, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(row.keys()))
        if not file_exists:
            w.writeheader()
        w.writerow(row)

def clear_gpu():
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.ipc_collect()

def main():
    RUNS_DIR.mkdir(parents=True, exist_ok=True)

    yolo_jobs = [
        ("yolov11m.pt", "yolov11m_e30")
    ]

    for weights, name in yolo_jobs:
        try:
            row = yolo_train(
                data_yaml=DATA_YAML,
                runs_dir=RUNS_DIR,
                weights=weights,
                run_name=name,
                imgsz=640,
                batch=10,
                epochs=30,
                workers=1,
                device=0,
            )
            append_row(row)
        except Exception as e:
            print(f"[ERROR] YOLO {name}: {e}")

if __name__ == "__main__":
    main()
