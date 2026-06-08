from __future__ import annotations

import os

from fastapi import FastAPI, File, Form, HTTPException, UploadFile

from .inference import VisionDetector, create_detector_from_env


app = FastAPI(title="Parking Detect Vision Service", version="1.0.0")
detector: VisionDetector | None = None


@app.on_event("startup")
def startup() -> None:
    global detector
    detector = create_detector_from_env()
    if os.getenv("VISION_SKIP_MODEL_LOAD", "false").lower() not in {"1", "true", "yes"}:
        detector.load_model()


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "modelLoaded": detector.model_loaded if detector else False,
    }


@app.get("/metrics")
def metrics() -> dict:
    if detector is None:
        return {"modelLoaded": False, "detectCount": 0, "avgLatencyMs": 0.0}
    return detector.metrics()


@app.post("/detect")
async def detect(
    file: UploadFile = File(...),
    roi: str = Form(""),
    camera_id: str = Form(""),
    roi_overlap: float = Form(0.35),
    track_iou: float = Form(0.3),
    dwell_frames: int = Form(1),
) -> dict:
    if detector is None:
        raise HTTPException(status_code=503, detail="vision detector is not initialized")
    try:
        image_bytes = await file.read()
        return detector.detect_image(
            image_bytes,
            roi_text=roi,
            camera_id=camera_id,
            roi_overlap=roi_overlap,
            track_iou=track_iou,
            dwell_frames=dwell_frames,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
