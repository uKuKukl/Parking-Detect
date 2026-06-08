import unittest

from decision_logic import (
    DetectionBox,
    DwellRoiDecisionEngine,
    bbox_iou,
    bbox_polygon_overlap_ratio,
)


class DecisionLogicTest(unittest.TestCase):
    def test_bbox_iou_partial_overlap(self):
        self.assertEqual(round(bbox_iou((0, 0, 10, 10), (5, 5, 15, 15)), 4), 0.1429)

    def test_bbox_polygon_overlap_ratio_inside_roi(self):
        roi = [(0, 0), (20, 0), (20, 20), (0, 20)]
        self.assertEqual(bbox_polygon_overlap_ratio((5, 5, 15, 15), roi, (40, 40)), 1.0)

    def test_bbox_polygon_overlap_ratio_partial_roi(self):
        roi = [(0, 0), (10, 0), (10, 20), (0, 20)]
        ratio = bbox_polygon_overlap_ratio((5, 5, 15, 15), roi, (40, 40))
        self.assertEqual(ratio, 0.6)

    def test_dwell_threshold_promotes_only_persistent_candidate(self):
        engine = DwellRoiDecisionEngine(
            roi_polygon=[(0, 0), (20, 0), (20, 20), (0, 20)],
            frame_size=(100, 100),
            roi_overlap_threshold=0.35,
            track_iou_threshold=0.3,
            dwell_frame_threshold=2,
        )

        first = engine.process_frame([
            DetectionBox(bbox=(40, 40, 60, 60), confidence=0.9, class_name="motorcycle")
        ])
        second = engine.process_frame([
            DetectionBox(bbox=(41, 40, 61, 60), confidence=0.88, class_name="motorcycle")
        ])

        self.assertEqual(first.confirmed_violations, [])
        self.assertEqual(len(second.confirmed_violations), 1)
        self.assertEqual(second.confirmed_violations[0].dwell_frames, 2)

    def test_legal_overlap_resets_dwell_count(self):
        engine = DwellRoiDecisionEngine(
            roi_polygon=[(0, 0), (70, 0), (70, 70), (0, 70)],
            frame_size=(100, 100),
            roi_overlap_threshold=0.35,
            track_iou_threshold=0.3,
            dwell_frame_threshold=2,
        )

        decision = engine.process_frame([
            DetectionBox(bbox=(10, 10, 40, 40), confidence=0.9, class_name="motorcycle")
        ])

        self.assertEqual(decision.confirmed_violations, [])
        self.assertEqual(decision.tracks[0].dwell_frames, 0)
        self.assertEqual(decision.tracks[0].reason, "INSIDE_LEGAL_ROI")


if __name__ == "__main__":
    unittest.main()
