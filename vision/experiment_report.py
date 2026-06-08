import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_OUTPUT_ROOT = Path(__file__).resolve().parent / "output"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a Markdown report from YOLO training and evaluation outputs.")
    parser.add_argument(
        "--metrics-dir",
        type=str,
        default=str(DEFAULT_OUTPUT_ROOT / "metrics"),
        help="Directory containing metrics_*.json files.",
    )
    parser.add_argument(
        "--training-dir",
        type=str,
        default=str(DEFAULT_OUTPUT_ROOT / "training"),
        help="Directory containing *_manifest.json files.",
    )
    parser.add_argument(
        "--out",
        type=str,
        default=str(DEFAULT_OUTPUT_ROOT / "experiment_report.md"),
        help="Markdown report output path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    metrics = load_json_files(Path(args.metrics_dir), "metrics_*.json")
    manifests = load_json_files(Path(args.training_dir), "*_manifest.json")
    report = build_report(metrics, manifests)
    out_path = Path(args.out).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report, encoding="utf-8")
    print(f"[INFO] Experiment report saved to: {out_path}")


def load_json_files(directory: Path, pattern: str) -> list[dict[str, Any]]:
    if not directory.exists():
        return []

    records: list[dict[str, Any]] = []
    for path in sorted(directory.glob(pattern)):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                data.setdefault("_sourceFile", str(path))
                records.append(data)
        except json.JSONDecodeError:
            continue
    return records


def build_report(metrics: list[dict[str, Any]], manifests: list[dict[str, Any]]) -> str:
    lines = [
        "# YOLO 模型训练与评估报告",
        "",
        "## 1. 实验概览",
        "",
        f"- 训练记录数: {len(manifests)}",
        f"- 评估记录数: {len(metrics)}",
        "- 评估指标: Precision、Recall、mAP@0.5、mAP@0.5:0.95、推理耗时。",
        "",
    ]

    lines.extend(render_training_table(manifests))
    lines.extend(render_metrics_table(metrics))
    lines.extend(render_resume_summary(metrics))
    return "\n".join(lines).rstrip() + "\n"


def render_training_table(manifests: list[dict[str, Any]]) -> list[str]:
    lines = [
        "## 2. 训练配置",
        "",
    ]
    if not manifests:
        lines.extend(["暂无训练记录。先运行 `python train_yolo.py --data <data.yaml>`。", ""])
        return lines

    lines.extend(
        [
            "| Run | Model | Epochs | Image Size | Batch | Device | Status | Notes |",
            "| --- | --- | ---: | ---: | ---: | --- | --- | --- |",
        ]
    )
    for item in manifests:
        lines.append(
            "| {run} | {model} | {epochs} | {imgsz} | {batch} | {device} | {status} | {notes} |".format(
                run=escape_md(item.get("runName", "-")),
                model=escape_md(item.get("model", "-")),
                epochs=item.get("epochs", "-"),
                imgsz=item.get("imgsz", "-"),
                batch=item.get("batch", "-"),
                device=escape_md(item.get("device", "-")),
                status=escape_md(item.get("status", "-")),
                notes=escape_md(item.get("notes", "")),
            )
        )
    lines.append("")
    return lines


def render_metrics_table(metrics: list[dict[str, Any]]) -> list[str]:
    lines = [
        "## 3. 评估指标",
        "",
    ]
    if not metrics:
        lines.extend(["暂无评估记录。先运行 `python eval_metrics.py --data <data.yaml>`。", ""])
        return lines

    sorted_metrics = sorted(metrics, key=lambda item: float_or_negative(item.get("map50_95")), reverse=True)
    lines.extend(
        [
            "| Rank | Run | Split | Precision | Recall | mAP@0.5 | mAP@0.5:0.95 | Avg Latency(ms) |",
            "| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for index, item in enumerate(sorted_metrics, start=1):
        lines.append(
            "| {rank} | {run} | {split} | {precision} | {recall} | {map50} | {map} | {latency} |".format(
                rank=index,
                run=escape_md(item.get("runName", Path(str(item.get("_sourceFile", "-"))).stem)),
                split=escape_md(item.get("split", "-")),
                precision=format_metric(item.get("precision")),
                recall=format_metric(item.get("recall")),
                map50=format_metric(item.get("map50")),
                map=format_metric(item.get("map50_95")),
                latency=format_metric(item.get("avgLatencyMs"), digits=2),
            )
        )
    lines.append("")
    return lines


def render_resume_summary(metrics: list[dict[str, Any]]) -> list[str]:
    lines = [
        "## 4. 简历表达建议",
        "",
    ]
    if not metrics:
        lines.extend(
            [
                "- 搭建 YOLOv8 模型训练与评估流水线，统一记录训练参数、Precision、Recall、mAP 和推理延迟，为后续模型迭代和误检分析提供可复现实验依据。",
                "",
            ]
        )
        return lines

    best = max(metrics, key=lambda item: float_or_negative(item.get("map50_95")))
    lines.extend(
        [
            "- 搭建 YOLOv8 模型训练与评估流水线，统一记录训练参数、Precision、Recall、mAP 和推理延迟，并生成实验对比报告。",
            "- 当前最佳评估结果: mAP@0.5={map50}, mAP@0.5:0.95={map}, Precision={precision}, Recall={recall}。".format(
                map50=format_metric(best.get("map50")),
                map=format_metric(best.get("map50_95")),
                precision=format_metric(best.get("precision")),
                recall=format_metric(best.get("recall")),
            ),
            "",
        ]
    )
    return lines


def escape_md(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ").strip()


def format_metric(value: Any, digits: int = 4) -> str:
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return "-"


def float_or_negative(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return -1.0


if __name__ == "__main__":
    main()
