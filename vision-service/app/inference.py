from __future__ import annotations

import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Any

import cv2
import numpy as np

VISION_DIR = Path(__file__).resolve().parents[2] / "vision"
if str(VISION_DIR) not in sys.path:
    sys.path.insert(0, str(VISION_DIR))

from decision_logic import DetectionBox, DwellRoiDecisionEngine


DEFAULT_CAMERA_ID = "CAM_SOUTH_GATE_01"
DEFAULT_LOCATION = "南门自行车停放区西侧"
DEFAULT_MODEL_PATH = Path(__file__).resolve().parents[2] / "vision" / "models" / "best.pt"
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parents[2] / "vision" / "output"


class VisionDetector:
    def __init__(
        self,
        model_path: str | Path,
        output_dir: str | Path,
        confidence_threshold: float = 0.5,
        nms_iou_threshold: float = 0.6,
    ) -> None:
        self.model_path = Path(model_path).expanduser().resolve()
        self.output_dir = Path(output_dir).expanduser().resolve()
        self.confidence_threshold = confidence_threshold
        self.nms_iou_threshold = nms_iou_threshold
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._model = None
        self._model_lock = Lock()
        self.detect_count = 0
        self.total_latency_ms = 0.0

    @property
    def model_loaded(self) -> bool:
        return self._model is not None

    def load_model(self):
        if self._model is not None:
            return self._model
        with self._model_lock:
            if self._model is None:
                from ultralytics import YOLO

                if not self.model_path.exists():
                    raise FileNotFoundError(f"YOLO model not found: {self.model_path}")
                self._model = YOLO(str(self.model_path))
        return self._model

    def detect_image(
        self,
        image_bytes: bytes,
        *,
        roi_text: str = "",
        camera_id: str = "",
        roi_overlap: float = 0.35,
        track_iou: float = 0.3,
        dwell_frames: int = 1,
    ) -> dict[str, Any]:
        start_time = time.perf_counter()
        model = self.load_model()
        image = decode_image(image_bytes)
        frame_height, frame_width = image.shape[:2]

        current_camera_id = camera_id.strip() or DEFAULT_CAMERA_ID
        roi_points, roi_reference_size, roi_name = parse_roi_payload(roi_text)
        location = roi_name or DEFAULT_LOCATION
        scaled_roi = scale_roi(roi_points, roi_reference_size, frame_width, frame_height)

        results = model.predict(
            source=image,
            conf=self.confidence_threshold,
            save=False,
            iou=self.nms_iou_threshold,
            stream=False,
            verbose=False,
        )
        if not results:
            raise RuntimeError("YOLO returned no prediction result")

        engine = DwellRoiDecisionEngine(
            roi_polygon=scaled_roi,
            frame_size=(frame_width, frame_height),
            roi_overlap_threshold=roi_overlap,
            track_iou_threshold=track_iou,
            dwell_frame_threshold=max(1, int(dwell_frames)),
        )
        detections = extract_detections(results[0])
        decision = engine.process_frame(detections)
        annotated_image = annotate_decision(image.copy(), scaled_roi, decision, engine)
        decision_summary = engine.to_summary()
        confirmed_violations = decision_summary.get("confirmedViolations", [])
        violation_count = len(confirmed_violations)
        max_confidence = max((float(item.get("confidence", 0.0)) for item in confirmed_violations), default=1.0)

        image_path = save_annotated_image(
            annotated_image,
            self.output_dir,
            current_camera_id,
            ok=violation_count == 0,
        )
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        self.detect_count += 1
        self.total_latency_ms += latency_ms

        decision_summary["serviceLatencyMs"] = latency_ms
        return build_detection_response(
            location=location,
            camera_id=current_camera_id,
            image_path=image_path,
            violation_count=violation_count,
            confidence=round(max_confidence, 2),
            decision_summary=decision_summary,
        )

    def metrics(self) -> dict[str, Any]:
        avg_latency = self.total_latency_ms / self.detect_count if self.detect_count else 0.0
        return {
            "modelLoaded": self.model_loaded,
            "modelPath": str(self.model_path),
            "detectCount": self.detect_count,
            "avgLatencyMs": round(avg_latency, 2),
        }


def create_detector_from_env() -> VisionDetector:
    return VisionDetector(
        model_path=os.getenv("VISION_MODEL_PATH", str(DEFAULT_MODEL_PATH)),
        output_dir=os.getenv("VISION_OUTPUT_DIR", str(DEFAULT_OUTPUT_DIR)),
        confidence_threshold=float(os.getenv("VISION_CONFIDENCE", "0.5")),
        nms_iou_threshold=float(os.getenv("VISION_NMS_IOU", "0.6")),
    )


def decode_image(image_bytes: bytes) -> np.ndarray:
    if not image_bytes:
        raise ValueError("上传图片为空")
    raw = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(raw, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("无法解析上传图片")
    return image


def parse_roi_payload(roi_text: str) -> tuple[list[tuple[float, float]] | None, tuple[int, int] | None, str | None]:
    if not roi_text:
        return None, None, None

    data = json.loads(roi_text)
    roi_name = None
    reference_size = None
    if isinstance(data, dict):
        points_raw = data.get("points", [])
        if data.get("name") and str(data.get("name")).strip():
            roi_name = str(data.get("name")).strip()
        ref_w = data.get("referenceWidth")
        ref_h = data.get("referenceHeight")
        if ref_w and ref_h:
            reference_size = (int(ref_w), int(ref_h))
    else:
        points_raw = data

    points = [tuple(point) for point in points_raw]
    return points, reference_size, roi_name


def scale_roi(
    roi_points: list[tuple[float, float]] | None,
    reference_size: tuple[int, int] | None,
    frame_width: int,
    frame_height: int,
) -> list[tuple[int, int]] | None:
    if not roi_points or len(roi_points) < 3:
        return None

    roi_np = np.array(roi_points, dtype=np.float32)
    if reference_size and len(reference_size) == 2:
        ref_width, ref_height = reference_size
        if ref_width <= 0 or ref_height <= 0:
            raise ValueError("ROI 参考尺寸非法")
        roi_np[:, 0] *= frame_width / ref_width
        roi_np[:, 1] *= frame_height / ref_height

    roi_np[:, 0] = np.clip(roi_np[:, 0], 0, frame_width - 1)
    roi_np[:, 1] = np.clip(roi_np[:, 1], 0, frame_height - 1)
    return [tuple(point) for point in np.round(roi_np).astype(int).tolist()]


def extract_detections(result: Any) -> list[DetectionBox]:
    detections = []
    names = getattr(result, "names", None) or {}
    for box in result.boxes:
        bbox = tuple(float(value) for value in box.xyxy[0].cpu().numpy())
        confidence = float(box.conf[0].item())
        class_id = int(box.cls[0].item()) if getattr(box, "cls", None) is not None else -1
        class_name = str(names.get(class_id, "vehicle")) if isinstance(names, dict) else "vehicle"
        detections.append(DetectionBox(bbox=bbox, confidence=confidence, class_name=class_name))
    return detections


def annotate_decision(image: np.ndarray, roi_points: list[tuple[int, int]] | None, decision: Any, engine: DwellRoiDecisionEngine) -> np.ndarray:
    if roi_points and len(roi_points) > 2:
        roi_np = np.array(roi_points, dtype=np.int32)
        cv2.polylines(image, [roi_np], isClosed=True, color=(0, 255, 0), thickness=3)

    confirmed_ids = {track.track_id for track in engine.confirmed_history.values()}
    for track in decision.tracks:
        x1, y1, x2, y2 = map(int, track.bbox)
        if track.track_id in confirmed_ids:
            color = (0, 0, 255)
            state = "VIOLATION"
        elif track.is_violation_candidate:
            color = (0, 215, 255)
            state = "CANDIDATE"
        else:
            color = (255, 255, 0)
            state = "LEGAL"
        cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
        label = f"T{track.track_id} {state} conf={track.confidence:.2f} dwell={track.dwell_frames} roi={track.legal_overlap_ratio:.2f}"
        cv2.putText(image, label, (x1, max(15, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.48, color, 2)
    return image


def save_annotated_image(image: np.ndarray, output_dir: Path, camera_id: str, ok: bool) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    suffix = "OK_" if ok else ""
    safe_camera_id = re.sub(r"[^A-Za-z0-9_-]", "_", camera_id or DEFAULT_CAMERA_ID)
    save_path = output_dir / f"violation_{safe_camera_id}_{suffix}{timestamp}.jpg"
    cv2.imwrite(str(save_path), image)
    return str(save_path)


def build_detection_response(
    *,
    location: str,
    camera_id: str,
    image_path: str,
    violation_count: int,
    confidence: float,
    decision_summary: dict[str, Any],
) -> dict[str, Any]:
    return {
        "detectTime": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "location": f"{location} (当前画面共发现 {violation_count} 辆违停)",
        "imagePath": image_path,
        "cameraId": camera_id,
        "confidence": confidence,
        "decisionDetails": json.dumps(decision_summary, ensure_ascii=False),
        "violationCount": violation_count,
        "annotatedImagePath": image_path,
        "tracks": decision_summary.get("tracks", []),
        "confirmedViolations": decision_summary.get("confirmedViolations", []),
    }
