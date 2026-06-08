import unittest

from experiment_report import build_report


class ExperimentReportTest(unittest.TestCase):
    def test_build_report_ranks_metrics_by_map50_95(self):
        report = build_report(
            metrics=[
                {
                    "runName": "baseline",
                    "split": "test",
                    "precision": 0.81,
                    "recall": 0.72,
                    "map50": 0.86,
                    "map50_95": 0.51,
                    "avgLatencyMs": 11.2,
                },
                {
                    "runName": "imgsz960",
                    "split": "test",
                    "precision": 0.84,
                    "recall": 0.76,
                    "map50": 0.89,
                    "map50_95": 0.58,
                    "avgLatencyMs": 14.7,
                },
            ],
            manifests=[
                {
                    "runName": "imgsz960",
                    "model": "yolov8n.pt",
                    "epochs": 50,
                    "imgsz": 960,
                    "batch": 8,
                    "device": "0",
                    "status": "completed",
                    "notes": "larger input",
                }
            ],
        )

        first_metric_row = next(line for line in report.splitlines() if line.startswith("| 1 |"))
        self.assertIn("imgsz960", first_metric_row)
        self.assertIn("mAP@0.5=0.8900", report)
        self.assertIn("mAP@0.5:0.95=0.5800", report)

    def test_build_report_handles_empty_records(self):
        report = build_report(metrics=[], manifests=[])

        self.assertIn("暂无训练记录", report)
        self.assertIn("暂无评估记录", report)
        self.assertIn("搭建 YOLOv8 模型训练与评估流水线", report)


if __name__ == "__main__":
    unittest.main()
