from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import cv2
import numpy as np


BBox = tuple[float, float, float, float]
Point = tuple[float, float]


@dataclass
class DetectionBox:
    bbox: BBox
    confidence: float
    class_name: str = "vehicle"


@dataclass
class DecisionTrack:
    track_id: int
    bbox: BBox
    confidence: float
    class_name: str
    legal_overlap_ratio: float
    dwell_frames: int
    max_dwell_frames: int
    missed_frames: int
    is_violation_candidate: bool
    reason: str

    def to_dict(self) -> dict:
        return {
            "trackId": self.track_id,
            "bbox": [round(value, 2) for value in self.bbox],
            "confidence": round(self.confidence, 4),
            "className": self.class_name,
            "legalOverlapRatio": round(self.legal_overlap_ratio, 4),
            "dwellFrames": self.dwell_frames,
            "maxDwellFrames": self.max_dwell_frames,
            "missedFrames": self.missed_frames,
            "violationCandidate": self.is_violation_candidate,
            "reason": self.reason,
        }


@dataclass
class FrameDecision:
    frame_index: int
    tracks: list[DecisionTrack]
    confirmed_violations: list[DecisionTrack]

    def to_dict(self) -> dict:
        return {
            "frameIndex": self.frame_index,
            "tracks": [track.to_dict() for track in self.tracks],
            "confirmedViolations": [track.to_dict() for track in self.confirmed_violations],
        }


def bbox_area(bbox: BBox) -> float:
    x1, y1, x2, y2 = bbox
    return max(0.0, x2 - x1) * max(0.0, y2 - y1)


def bbox_iou(first: BBox, second: BBox) -> float:
    fx1, fy1, fx2, fy2 = first
    sx1, sy1, sx2, sy2 = second

    ix1 = max(fx1, sx1)
    iy1 = max(fy1, sy1)
    ix2 = min(fx2, sx2)
    iy2 = min(fy2, sy2)

    intersection = bbox_area((ix1, iy1, ix2, iy2))
    union = bbox_area(first) + bbox_area(second) - intersection
    if union <= 0:
        return 0.0
    return intersection / union


def bbox_polygon_overlap_ratio(bbox: BBox, polygon: Iterable[Point] | None, frame_size: tuple[int, int]) -> float:
    points = list(polygon or [])
    if len(points) < 3:
        return 0.0

    width, height = frame_size
    if width <= 0 or height <= 0:
        return 0.0

    x1, y1, x2, y2 = _clip_bbox(bbox, width, height)
    if x2 <= x1 or y2 <= y1:
        return 0.0

    roi_mask = np.zeros((height, width), dtype=np.uint8)
    bbox_mask = np.zeros((height, width), dtype=np.uint8)
    roi_points = np.array(points, dtype=np.int32)

    cv2.fillPoly(roi_mask, [roi_points], 255)
    cv2.rectangle(bbox_mask, (x1, y1), (x2 - 1, y2 - 1), 255, thickness=-1)

    bbox_pixels = cv2.countNonZero(bbox_mask)
    if bbox_pixels == 0:
        return 0.0

    overlap_pixels = cv2.countNonZero(cv2.bitwise_and(roi_mask, bbox_mask))
    return round(overlap_pixels / bbox_pixels, 6)


class DwellRoiDecisionEngine:
    def __init__(
        self,
        roi_polygon: Iterable[Point] | None,
        frame_size: tuple[int, int],
        roi_overlap_threshold: float = 0.35,
        track_iou_threshold: float = 0.3,
        dwell_frame_threshold: int = 1,
        max_missed_frames: int = 5,
    ) -> None:
        self.roi_polygon = list(roi_polygon or [])
        self.frame_size = frame_size
        self.roi_overlap_threshold = _clamp(roi_overlap_threshold, 0.0, 1.0)
        self.track_iou_threshold = _clamp(track_iou_threshold, 0.0, 1.0)
        self.dwell_frame_threshold = max(1, int(dwell_frame_threshold))
        self.max_missed_frames = max(0, int(max_missed_frames))
        self.frame_index = 0
        self.next_track_id = 1
        self.tracks: list[DecisionTrack] = []
        self.confirmed_history: dict[int, DecisionTrack] = {}
        self.total_detections = 0
        self.last_decision = FrameDecision(frame_index=0, tracks=[], confirmed_violations=[])

    def process_frame(self, detections: list[DetectionBox]) -> FrameDecision:
        self.frame_index += 1
        self.total_detections += len(detections)

        matched_track_ids: set[int] = set()
        updated_tracks: list[DecisionTrack] = []

        for detection in sorted(detections, key=lambda item: item.confidence, reverse=True):
            matched_track = self._match_track(detection, matched_track_ids)
            updated_track = self._build_track(detection, matched_track)
            matched_track_ids.add(updated_track.track_id)
            updated_tracks.append(updated_track)

        for old_track in self.tracks:
            if old_track.track_id in matched_track_ids:
                continue
            missed = DecisionTrack(
                track_id=old_track.track_id,
                bbox=old_track.bbox,
                confidence=old_track.confidence,
                class_name=old_track.class_name,
                legal_overlap_ratio=old_track.legal_overlap_ratio,
                dwell_frames=0,
                max_dwell_frames=old_track.max_dwell_frames,
                missed_frames=old_track.missed_frames + 1,
                is_violation_candidate=False,
                reason="MISSING_THIS_FRAME",
            )
            if missed.missed_frames <= self.max_missed_frames:
                updated_tracks.append(missed)

        self.tracks = updated_tracks
        confirmed = [
            track for track in self.tracks
            if track.is_violation_candidate and track.dwell_frames >= self.dwell_frame_threshold
        ]
        for track in confirmed:
            previous = self.confirmed_history.get(track.track_id)
            if previous is None or track.max_dwell_frames >= previous.max_dwell_frames:
                self.confirmed_history[track.track_id] = track
        self.last_decision = FrameDecision(
            frame_index=self.frame_index,
            tracks=list(self.tracks),
            confirmed_violations=confirmed,
        )
        return self.last_decision

    def to_summary(self) -> dict:
        return {
            "algorithm": "YOLOv8 + ROI overlap + IoU tracking + dwell frames",
            "roiOverlapThreshold": self.roi_overlap_threshold,
            "trackIouThreshold": self.track_iou_threshold,
            "dwellFrameThreshold": self.dwell_frame_threshold,
            "processedFrames": self.frame_index,
            "totalDetections": self.total_detections,
            "activeTrackCount": len(self.tracks),
            "confirmedViolationCount": len(self.confirmed_history),
            "tracks": [track.to_dict() for track in self.tracks],
            "confirmedViolations": [track.to_dict() for track in self.confirmed_history.values()],
        }

    def _match_track(self, detection: DetectionBox, matched_track_ids: set[int]) -> DecisionTrack | None:
        best_track = None
        best_iou = 0.0
        for track in self.tracks:
            if track.track_id in matched_track_ids:
                continue
            score = bbox_iou(detection.bbox, track.bbox)
            if score >= self.track_iou_threshold and score > best_iou:
                best_iou = score
                best_track = track
        return best_track

    def _build_track(self, detection: DetectionBox, previous: DecisionTrack | None) -> DecisionTrack:
        overlap_ratio = bbox_polygon_overlap_ratio(detection.bbox, self.roi_polygon, self.frame_size)
        has_roi = len(self.roi_polygon) >= 3
        is_legal = has_roi and overlap_ratio >= self.roi_overlap_threshold
        is_candidate = not is_legal
        dwell_frames = 0
        if is_candidate:
            dwell_frames = (previous.dwell_frames + 1) if previous else 1

        max_dwell_frames = max(previous.max_dwell_frames if previous else 0, dwell_frames)
        if is_legal:
            reason = "INSIDE_LEGAL_ROI"
        elif has_roi:
            reason = "OUTSIDE_LEGAL_ROI"
        else:
            reason = "NO_ROI_FULL_FRAME_RESTRICTED"

        return DecisionTrack(
            track_id=previous.track_id if previous else self.next_track_id_and_increment(),
            bbox=detection.bbox,
            confidence=detection.confidence,
            class_name=detection.class_name,
            legal_overlap_ratio=overlap_ratio,
            dwell_frames=dwell_frames,
            max_dwell_frames=max_dwell_frames,
            missed_frames=0,
            is_violation_candidate=is_candidate,
            reason=reason,
        )

    def next_track_id_and_increment(self) -> int:
        track_id = self.next_track_id
        self.next_track_id += 1
        return track_id


def _clip_bbox(bbox: BBox, width: int, height: int) -> tuple[int, int, int, int]:
    x1, y1, x2, y2 = bbox
    return (
        max(0, min(width, int(round(x1)))),
        max(0, min(height, int(round(y1)))),
        max(0, min(width, int(round(x2)))),
        max(0, min(height, int(round(y2)))),
    )


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, float(value)))
