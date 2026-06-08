import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "vision"))
sys.path.insert(0, str(ROOT / "vision-service"))

from app.inference import build_detection_response, parse_roi_payload, scale_roi


class InferenceHelperTest(unittest.TestCase):
    def test_parse_roi_payload_reads_points_reference_size_and_name(self):
        payload = json.dumps(
            {
                "name": "南门停车区",
                "referenceWidth": 100,
                "referenceHeight": 200,
                "points": [[10, 20], [90, 20], [90, 160], [10, 160]],
            },
            ensure_ascii=False,
        )

        points, reference_size, name = parse_roi_payload(payload)

        self.assertEqual(name, "南门停车区")
        self.assertEqual(reference_size, (100, 200))
        self.assertEqual(points[0], (10, 20))

    def test_scale_roi_maps_reference_size_to_frame_size(self):
        scaled = scale_roi(
            [(10, 20), (90, 20), (90, 160), (10, 160)],
            (100, 200),
            frame_width=200,
            frame_height=100,
        )

        self.assertEqual(scaled, [(20, 10), (180, 10), (180, 80), (20, 80)])

    def test_build_detection_response_matches_backend_payload_shape(self):
        response = build_detection_response(
            location="南门停车区",
            camera_id="CAM_1",
            image_path="D:/tmp/annotated.jpg",
            violation_count=2,
            confidence=0.91,
            decision_summary={"confirmedViolationCount": 2},
        )

        self.assertIn("当前画面共发现 2 辆违停", response["location"])
        self.assertEqual(response["cameraId"], "CAM_1")
        self.assertEqual(response["confidence"], 0.91)
        self.assertEqual(json.loads(response["decisionDetails"])["confirmedViolationCount"], 2)
        self.assertIn("tracks", response)
        self.assertIn("confirmedViolations", response)


if __name__ == "__main__":
    unittest.main()
