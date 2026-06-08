import argparse
import json
from datetime import datetime
from pathlib import Path

from ultralytics import YOLO


DEFAULT_OUTPUT_ROOT = Path(__file__).resolve().parent / "output"
DEFAULT_PRETRAINED_MODEL = "yolov8n.pt"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train a YOLO model and save an experiment manifest.")
    parser.add_argument("--data", type=str, required=True, help="Path to YOLO data.yaml.")
    parser.add_argument("--model", type=str, default=DEFAULT_PRETRAINED_MODEL, help="Pretrained model or weights path.")
    parser.add_argument("--epochs", type=int, default=50, help="Training epochs.")
    parser.add_argument("--imgsz", type=int, default=960, help="Training image size.")
    parser.add_argument("--batch", type=int, default=8, help="Training batch size.")
    parser.add_argument("--device", type=str, default="0", help="CUDA device id or 'cpu'.")
    parser.add_argument("--workers", type=int, default=4, help="Data loader workers.")
    parser.add_argument("--patience", type=int, default=20, help="Early stopping patience.")
    parser.add_argument("--name", type=str, default="", help="Experiment name. Defaults to train_<timestamp>.")
    parser.add_argument("--notes", type=str, default="", help="Short experiment notes for resume/interview review.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    parser.add_argument("--dry-run", action="store_true", help="Only validate paths and write the planned manifest.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data_path = Path(args.data).expanduser().resolve()
    if not data_path.exists():
        raise FileNotFoundError(f"Dataset yaml not found: {data_path}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_name = args.name.strip() or f"train_{timestamp}"
    project_dir = DEFAULT_OUTPUT_ROOT / "training"
    project_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "runName": run_name,
        "createdAt": datetime.now().isoformat(timespec="seconds"),
        "data": str(data_path),
        "model": args.model,
        "epochs": args.epochs,
        "imgsz": args.imgsz,
        "batch": args.batch,
        "device": args.device,
        "workers": args.workers,
        "patience": args.patience,
        "seed": args.seed,
        "notes": args.notes,
        "dryRun": args.dry_run,
        "status": "planned",
    }

    if args.dry_run:
        manifest_path = write_manifest(project_dir, run_name, manifest)
        print(f"[INFO] Dry run only. Manifest saved to: {manifest_path}")
        return

    print(f"[INFO] Loading model: {args.model}")
    print(f"[INFO] Training data: {data_path}")
    model = YOLO(args.model)
    result = model.train(
        data=str(data_path),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        workers=args.workers,
        patience=args.patience,
        seed=args.seed,
        project=str(project_dir),
        name=run_name,
        exist_ok=True,
        plots=True,
        verbose=True,
    )

    save_dir = Path(getattr(result, "save_dir", project_dir / run_name))
    manifest.update(
        {
            "status": "completed",
            "saveDir": str(save_dir),
            "weights": {
                "best": str(save_dir / "weights" / "best.pt"),
                "last": str(save_dir / "weights" / "last.pt"),
            },
        }
    )
    manifest_path = write_manifest(project_dir, run_name, manifest)

    print("\n========== Training Summary ==========")
    print(f"Run name      : {run_name}")
    print(f"Output dir    : {save_dir}")
    print(f"Best weights  : {manifest['weights']['best']}")
    print(f"Manifest JSON : {manifest_path}")


def write_manifest(project_dir: Path, run_name: str, manifest: dict) -> Path:
    manifest_path = project_dir / f"{run_name}_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest_path


if __name__ == "__main__":
    main()
