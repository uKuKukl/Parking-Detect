import argparse
import json
import os
import re
import sys
from datetime import datetime

import cv2
import numpy as np
import requests
from ultralytics import YOLO

from decision_logic import DetectionBox, DwellRoiDecisionEngine


# ================= 配置区域 =================
MODEL_PATH = "models/best.pt"
CAMERA_ID = "CAM_SOUTH_GATE_01"
LOCATION_STR = "南门自行车停放区西侧"
API_URL = "http://127.0.0.1:8080/api/violations/upload"
CONFIDENCE_THRESHOLD = 0.5
NMS_IOU_THRESHOLD = 0.6
TARGET_CLASSES = None

# 电子围栏表示“允许停放区域”。没有 ROI 时，系统按全图禁停处理。
LEGAL_PARKING_ZONE = None
ROI_REFERENCE_SIZE = None

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)


def parse_args():
    parser = argparse.ArgumentParser(description="YOLO 违规停车检测")
    parser.add_argument("--source", type=str, default="test_image.jpg", help="图片、视频、摄像头编号或视频流地址")
    parser.add_argument("--roi", type=str, default="", help="后端传入的动态 ROI JSON")
    parser.add_argument("--camera-id", type=str, default="", help="当前围栏绑定的摄像头编号")
    parser.add_argument("--conf", type=float, default=None, help="临时覆盖置信度阈值")
    parser.add_argument("--roi-overlap", type=float, default=0.35, help="bbox 与合法 ROI 的最小重叠比例")
    parser.add_argument("--track-iou", type=float, default=0.3, help="连续帧目标关联 IoU 阈值")
    parser.add_argument("--dwell-frames", type=int, default=None, help="判定违停需要连续停留的帧数")
    parser.add_argument("--max-frames", type=int, default=120, help="视频/摄像头输入最多处理帧数")
    return parser.parse_args()


def main():
    args = parse_args()

    global CONFIDENCE_THRESHOLD
    if args.conf is not None:
        CONFIDENCE_THRESHOLD = args.conf
        print(f"[INFO] 覆盖置信度阈值为: {CONFIDENCE_THRESHOLD}")

    current_location_str = LOCATION_STR
    current_camera_id = args.camera_id.strip() if args.camera_id else CAMERA_ID
    roi_points, roi_reference_size, roi_name = parse_roi(args.roi)
    if roi_name:
        current_location_str = roi_name

    test_source = args.source
    if isinstance(test_source, str) and not os.path.exists(test_source) and not is_stream_source(test_source):
        print("[WARN] 未找到测试图片，请在 vision 目录下放置一张 test_image.jpg，或通过 --source 指定图片/视频/摄像头。")
        return

    stream_input = is_stream_source(test_source)
    dwell_frame_threshold = args.dwell_frames if args.dwell_frames is not None else (3 if stream_input else 1)

    print(f"[INFO] 正在加载 YOLO 模型: {MODEL_PATH}")
    model = YOLO(MODEL_PATH)
    source_for_model = int(test_source) if str(test_source).isdigit() and stream_input else test_source

    print(f"[INFO] 准备检测数据源: {test_source}")
    print(
        "[INFO] 判定参数: "
        f"roi_overlap={args.roi_overlap}, track_iou={args.track_iou}, dwell_frames={dwell_frame_threshold}"
    )

    try:
        prediction_stream = model.predict(
            source=source_for_model,
            conf=CONFIDENCE_THRESHOLD,
            save=False,
            classes=TARGET_CLASSES,
            iou=NMS_IOU_THRESHOLD,
            stream=True,
            verbose=False,
        )

        engine = None
        last_decision = None
        last_annotated_img = None
        representative_img = None
        frame_count = 0
        scaled_roi = None

        for result in prediction_stream:
            frame_count += 1
            frame_height, frame_width = result.orig_img.shape[:2]

            if engine is None:
                scaled_roi = scale_roi(roi_points, roi_reference_size, frame_width, frame_height)
                engine = DwellRoiDecisionEngine(
                    roi_polygon=scaled_roi,
                    frame_size=(frame_width, frame_height),
                    roi_overlap_threshold=args.roi_overlap,
                    track_iou_threshold=args.track_iou,
                    dwell_frame_threshold=dwell_frame_threshold,
                )
                if scaled_roi:
                    print(f"[INFO] 成功加载电子围栏，共 {len(scaled_roi)} 个顶点")
                else:
                    print("[INFO] 未加载电子围栏，当前按全图禁停处理")

            detections = extract_detections(result)
            last_decision = engine.process_frame(detections)
            last_annotated_img = annotate_decision(result.orig_img.copy(), scaled_roi, last_decision, engine)

            if last_decision.confirmed_violations:
                representative_img = last_annotated_img.copy()

            if not stream_input:
                break
            if frame_count >= max(1, args.max_frames):
                print(f"[INFO] 已达到最大处理帧数: {args.max_frames}")
                break

        if engine is None or last_decision is None or last_annotated_img is None:
            print("[ERROR] 未获得任何检测结果")
            sys.exit(1)

        decision_summary = engine.to_summary()
        confirmed_violations = decision_summary.get("confirmedViolations", [])
        obj_count = len(confirmed_violations)
        save_img = representative_img if representative_img is not None else last_annotated_img

        if obj_count > 0:
            print(f"[INFO] 检测到满足滞留条件的违规车辆: {obj_count} 辆")
            max_conf = max(float(item.get("confidence", 0.0)) for item in confirmed_violations)
            save_path = save_annotated_image(save_img, current_camera_id, ok=False)
            payload = build_payload(
                current_location_str,
                current_camera_id,
                save_path,
                obj_count,
                round(max_conf, 2),
                decision_summary,
            )
            post_payload(payload, success_message=f"{obj_count} 辆违停的汇总数据已成功推送到后端！")
        else:
            print("[INFO] 当前输入未发现满足 ROI + 滞留阈值的违规车辆，仍上报 0 违规记录供人工复核。")
            save_path = save_annotated_image(save_img, current_camera_id, ok=True)
            payload = build_payload(
                current_location_str,
                current_camera_id,
                save_path,
                0,
                1.0,
                decision_summary,
            )
            post_payload(payload, success_message="0 辆违停的汇总数据已成功推送到后端！")

    except Exception as exc:
        print(f"[ERROR] 检测运行出错: {exc}")
        sys.exit(1)


def parse_roi(roi_text):
    global LEGAL_PARKING_ZONE, ROI_REFERENCE_SIZE
    LEGAL_PARKING_ZONE = None
    ROI_REFERENCE_SIZE = None

    if not roi_text:
        return None, None, None

    try:
        raw_text = roi_text.strip()
        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError:
            fixed = re.sub(r'([{,]\s*)([a-zA-Z_]\w*)(\s*:)', r'\1"\2"\3', raw_text)
            fixed = re.sub(
                r'("name"\s*:\s*)([^"\[\{][^,}\]]*)',
                lambda match: f'{match.group(1)}"{match.group(2).strip()}"',
                fixed,
            )
            data = json.loads(fixed)

        roi_name = None
        if isinstance(data, dict):
            points_raw = data.get("points", [])
            ref_w = data.get("referenceWidth")
            ref_h = data.get("referenceHeight")
            if data.get("name") and str(data.get("name")).strip():
                roi_name = str(data.get("name")).strip()
            if ref_w and ref_h:
                ROI_REFERENCE_SIZE = (int(ref_w), int(ref_h))
        else:
            points_raw = data

        LEGAL_PARKING_ZONE = [tuple(point) for point in points_raw]
        return LEGAL_PARKING_ZONE, ROI_REFERENCE_SIZE, roi_name
    except Exception as exc:
        print(f"[ERROR] 解析动态电子围栏失败: {exc}")
        print(f"[DEBUG] 原始 ROI 字符串: {repr(roi_text[:300])}")
        return None, None, None


def scale_roi(roi_points, reference_size, frame_width, frame_height):
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


def extract_detections(result):
    detections = []
    names = getattr(result, "names", None) or {}
    for box in result.boxes:
        bbox = tuple(float(value) for value in box.xyxy[0].cpu().numpy())
        confidence = float(box.conf[0].item())
        class_id = int(box.cls[0].item()) if getattr(box, "cls", None) is not None else -1
        class_name = str(names.get(class_id, "vehicle")) if isinstance(names, dict) else "vehicle"
        detections.append(DetectionBox(bbox=bbox, confidence=confidence, class_name=class_name))
    return detections


def annotate_decision(image, roi_points, decision, engine):
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
        label = (
            f"T{track.track_id} {state} "
            f"conf={track.confidence:.2f} dwell={track.dwell_frames} roi={track.legal_overlap_ratio:.2f}"
        )
        cv2.putText(image, label, (x1, max(15, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.48, color, 2)

    return image


def save_annotated_image(image, camera_id, ok):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = "OK_" if ok else ""
    safe_camera_id = re.sub(r"[^A-Za-z0-9_-]", "_", camera_id or CAMERA_ID)
    save_filename = f"violation_{safe_camera_id}_{suffix}{timestamp}.jpg"
    save_path = os.path.join(OUTPUT_DIR, save_filename)
    cv2.imwrite(save_path, image)
    print(f"[INFO] 截图已保存至: {save_path}")
    return save_path


def build_payload(location, camera_id, image_path, violation_count, confidence, decision_summary):
    return {
        "detectTime": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "location": f"{location} (当前画面共发现 {violation_count} 辆违停)",
        "imagePath": image_path,
        "cameraId": camera_id,
        "confidence": confidence,
        "decisionDetails": json.dumps(decision_summary, ensure_ascii=False),
    }


def post_payload(payload, success_message):
    print(f"[INFO] 准备推送到后端: {payload}")
    try:
        resp = requests.post(API_URL, json=payload, timeout=5)
        if resp.status_code == 200:
            print(f"[SUCCESS] {success_message}")
        else:
            print(f"[ERROR] 推送失败，HTTP 状态码: {resp.status_code}")
            sys.exit(1)
    except Exception as exc:
        print(f"[ERROR] 连接后端失败: {exc}")
        sys.exit(1)


def is_stream_source(source):
    text = str(source).strip().lower()
    if text.isdigit():
        return True
    if text.startswith(("rtsp://", "rtmp://", "http://", "https://")):
        return True
    return os.path.splitext(text)[1] in {
        ".mp4",
        ".avi",
        ".mov",
        ".mkv",
        ".wmv",
        ".flv",
        ".m4v",
    }


if __name__ == "__main__":
    main()
