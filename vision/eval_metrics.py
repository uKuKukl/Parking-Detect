import argparse
import json
from datetime import datetime
from pathlib import Path

from ultralytics import YOLO


DEFAULT_MODEL = Path(__file__).resolve().parent / "models" / "best.pt"
DEFAULT_OUTPUT_ROOT = Path(__file__).resolve().parent / "output"
DISPLAY_CLASS_NAME = "motorcycle"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate YOLO model metrics on a dataset split.")
    parser.add_argument(
        "--model",
        type=str,
        default=str(DEFAULT_MODEL),
        help="Path to the trained YOLO weights file.",
    )
    parser.add_argument(
        "--data",
        type=str,
        required=True,
        help="Path to the YOLO data.yaml used for validation/testing.",
    )
    parser.add_argument(
        "--split",
        type=str,
        default="test",
        choices=["train", "val", "test"],
        help="Dataset split to evaluate.",
    )
    parser.add_argument("--imgsz", type=int, default=960, help="Validation image size.")
    parser.add_argument("--batch", type=int, default=8, help="Validation batch size.")
    parser.add_argument("--device", type=str, default="0", help="CUDA device id or 'cpu'.")
    parser.add_argument("--conf", type=float, default=0.25, help="Confidence threshold.")
    parser.add_argument("--iou", type=float, default=0.7, help="IoU threshold for NMS.")
    parser.add_argument("--run-name", type=str, default="", help="Evaluation run name. Defaults to metrics_<split>_<timestamp>.")
    parser.add_argument("--notes", type=str, default="", help="Short evaluation notes for experiment reports.")
    parser.add_argument(
        "--save-json",
        action="store_true",
        help="Whether to export COCO-style JSON predictions when supported.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    model_path = Path(args.model).expanduser().resolve()
    data_path = Path(args.data).expanduser().resolve()

    if not model_path.exists():
        raise FileNotFoundError(f"Model weights not found: {model_path}")
    if not data_path.exists():
        raise FileNotFoundError(f"Dataset yaml not found: {data_path}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_name = args.run_name.strip() or f"metrics_{args.split}_{timestamp}"
    project_dir = DEFAULT_OUTPUT_ROOT / "metrics"
    project_dir.mkdir(parents=True, exist_ok=True)

    print(f"[INFO] Loading model: {model_path}")
    print(f"[INFO] Evaluating split: {args.split}")
    print(f"[INFO] Using dataset yaml: {data_path}")

    model = YOLO(str(model_path))
    if getattr(model, "names", None) and len(model.names) == 1:
        model.names = {0: DISPLAY_CLASS_NAME}
        print(f"[INFO] Overriding single-class display name to: {DISPLAY_CLASS_NAME}")

    results = model.val(
        data=str(data_path),
        split=args.split,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        conf=args.conf,
        iou=args.iou,
        project=str(project_dir),
        name=run_name,
        exist_ok=True,
        plots=True,
        save_json=args.save_json,
        verbose=True,
    )

    speed = getattr(results, "speed", {}) or {}
    preprocess_ms = float(speed.get("preprocess", 0.0))
    inference_ms = float(speed.get("inference", 0.0))
    postprocess_ms = float(speed.get("postprocess", 0.0))
    metrics = {
        "runName": run_name,
        "evaluatedAt": datetime.now().isoformat(timespec="seconds"),
        "model": str(model_path),
        "data": str(data_path),
        "split": args.split,
        "imgsz": args.imgsz,
        "batch": args.batch,
        "device": args.device,
        "conf": args.conf,
        "iou": args.iou,
        "precision": round(float(results.box.mp), 6),
        "recall": round(float(results.box.mr), 6),
        "map50": round(float(results.box.map50), 6),
        "map50_95": round(float(results.box.map), 6),
        "preprocessMs": round(preprocess_ms, 4),
        "inferenceMs": round(inference_ms, 4),
        "postprocessMs": round(postprocess_ms, 4),
        "avgLatencyMs": round(preprocess_ms + inference_ms + postprocess_ms, 4),
        "save_dir": str(results.save_dir),
        "notes": args.notes,
    }

    metrics_path = project_dir / f"{run_name}.json"
    metrics_path.write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\n========== Evaluation Summary ==========")
    print(f"Precision : {metrics['precision']:.4f}")
    print(f"Recall    : {metrics['recall']:.4f}")
    print(f"mAP@0.5   : {metrics['map50']:.4f}")
    print(f"mAP@0.5:0.95 : {metrics['map50_95']:.4f}")
    print(f"Avg latency(ms) : {metrics['avgLatencyMs']:.2f}")
    print(f"Plots saved to : {metrics['save_dir']}")
    print(f"Metrics JSON   : {metrics_path}")


if __name__ == "__main__":
    main()
