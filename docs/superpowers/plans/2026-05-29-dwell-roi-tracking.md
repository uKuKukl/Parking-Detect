# Dwell ROI Tracking Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a resume-worthy violation decision algorithm that combines ROI overlap, IoU-based lightweight tracking, and dwell-frame filtering, then expose its decision details in backend, frontend, and documentation.

**Architecture:** Keep YOLO inference inside `vision/vision.py`, move pure decision logic into `vision/decision_logic.py`, persist explanation JSON in `parking_violations.decision_details`, and show it in the audit UI. The feature stays backward-compatible with existing single-image upload by defaulting dwell frames to 1 for image files and 3 for streams unless overridden.

**Tech Stack:** Python 3, OpenCV, NumPy, Ultralytics YOLO, Spring Boot 3, MyBatis-Plus, MySQL, Vue 3, Element Plus.

---

## File Structure

- Create `vision/decision_logic.py`: Pure Python/OpenCV decision module for bbox area, IoU, ROI overlap, track association, dwell counting, and JSON-friendly summaries.
- Create `vision/test_decision_logic.py`: Unit tests for geometry, tracking, and dwell filtering.
- Modify `vision/vision.py`: Parse new CLI flags, convert YOLO boxes to decision objects, process one or more frames, annotate tracks, and upload `decisionDetails`.
- Modify `backend/db/schema.sql`: Add `decision_details TEXT COMMENT '算法判定依据 JSON'`.
- Modify `backend/db/rebuild.sql`: Add the same column if the rebuild script has the `parking_violations` table.
- Modify `backend/src/main/java/com/parking/detect/entity/ParkingViolation.java`: Add `private String decisionDetails;`.
- Modify `backend/src/main/java/com/parking/detect/controller/ParkingViolationController.java`: Include decision details in Word/Excel exports.
- Modify `frontend/src/views/AuditView.vue`: Add a “判定依据” button and dialog that parses and displays decision JSON.
- Create `docs/违规停车判定算法优化说明.md`: Chinese explanation of the algorithm, code path, run commands, and resume bullets.

## Task 1: Add Pure Decision Logic

**Files:**
- Create: `vision/decision_logic.py`
- Create: `vision/test_decision_logic.py`

- [ ] **Step 1: Create failing tests for geometry and dwell behavior**

Create `vision/test_decision_logic.py` with tests covering:

```python
from decision_logic import (
    DetectionBox,
    DwellRoiDecisionEngine,
    bbox_iou,
    bbox_polygon_overlap_ratio,
)


def test_bbox_iou_partial_overlap():
    assert round(bbox_iou((0, 0, 10, 10), (5, 5, 15, 15)), 4) == 0.1429


def test_bbox_polygon_overlap_ratio_inside_roi():
    roi = [(0, 0), (20, 0), (20, 20), (0, 20)]
    assert bbox_polygon_overlap_ratio((5, 5, 15, 15), roi, (40, 40)) == 1.0


def test_dwell_threshold_promotes_only_persistent_candidate():
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

    assert first.confirmed_violations == []
    assert len(second.confirmed_violations) == 1
    assert second.confirmed_violations[0].dwell_frames == 2
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```powershell
cd vision
python -m pytest test_decision_logic.py -q
```

Expected: fail because `decision_logic.py` does not exist.

- [ ] **Step 3: Implement `decision_logic.py`**

Implement:

```python
@dataclass
class DetectionBox:
    bbox: tuple[float, float, float, float]
    confidence: float
    class_name: str = "vehicle"

@dataclass
class DecisionTrack:
    track_id: int
    bbox: tuple[float, float, float, float]
    confidence: float
    class_name: str
    legal_overlap_ratio: float
    dwell_frames: int
    max_dwell_frames: int
    missed_frames: int
    is_violation_candidate: bool
    reason: str

class DwellRoiDecisionEngine:
    def process_frame(self, detections: list[DetectionBox]) -> FrameDecision:
        ...
```

The implementation must use `cv2.fillPoly` and `cv2.rectangle` masks for bbox/ROI overlap, greedy IoU matching for tracks, and `to_summary()` for JSON-friendly details.

- [ ] **Step 4: Run tests and verify pass**

Run:

```powershell
cd vision
python -m pytest test_decision_logic.py -q
```

Expected: all tests pass.

## Task 2: Integrate Decision Engine Into YOLO Script

**Files:**
- Modify: `vision/vision.py`

- [ ] **Step 1: Add CLI arguments**

Add:

```python
parser.add_argument("--roi-overlap", type=float, default=0.35, help="bbox 与合法 ROI 的最小重叠比例")
parser.add_argument("--track-iou", type=float, default=0.3, help="连续帧目标关联 IoU 阈值")
parser.add_argument("--dwell-frames", type=int, default=None, help="判定违停需要连续停留的帧数")
parser.add_argument("--max-frames", type=int, default=120, help="视频/摄像头输入最多处理帧数")
```

- [ ] **Step 2: Convert YOLO boxes to `DetectionBox`**

Use model class names if available, otherwise fallback to `"vehicle"`. Preserve max confidence for payload.

- [ ] **Step 3: Process image and stream inputs**

Use existing `model.predict` for image input. For video/camera, iterate over prediction results with `stream=True`, stop after `max_frames`, and use default dwell threshold 3. For image files, default dwell threshold 1.

- [ ] **Step 4: Upload `decisionDetails`**

Add this field to both violation and zero-violation payloads:

```python
"decisionDetails": json.dumps(decision_summary, ensure_ascii=False)
```

- [ ] **Step 5: Keep annotated image output**

Draw:

- Red boxes for confirmed violations with `T<id> dwell=<n> overlap=<r>`.
- Yellow boxes for candidate tracks that have not reached dwell threshold.
- Cyan boxes for legal ROI-overlap tracks.
- Green polygon for legal ROI.

## Task 3: Persist Decision Details in Backend

**Files:**
- Modify: `backend/db/schema.sql`
- Modify: `backend/db/rebuild.sql`
- Modify: `backend/src/main/java/com/parking/detect/entity/ParkingViolation.java`
- Modify: `backend/src/main/java/com/parking/detect/controller/ParkingViolationController.java`

- [ ] **Step 1: Add DB column**

In `parking_violations` table:

```sql
  `decision_details` TEXT COMMENT '算法判定依据 JSON',
```

- [ ] **Step 2: Add entity field**

In `ParkingViolation.java`:

```java
private String decisionDetails;
```

- [ ] **Step 3: Include in exports**

Word export should include a short “算法判定依据” section. Excel export should add a `判定依据` column.

- [ ] **Step 4: Compile backend**

Run:

```powershell
cd backend
mvn -q -DskipTests package
```

Expected: build succeeds.

## Task 4: Show Decision Details in Audit UI

**Files:**
- Modify: `frontend/src/views/AuditView.vue`

- [ ] **Step 1: Add table action**

Add a small button near image preview:

```vue
<el-button link type="info" @click="openDecisionDialog(scope.row)">
  查看判定依据
</el-button>
```

- [ ] **Step 2: Add dialog**

Display thresholds, processed frames, confirmed count, and track rows. If JSON parsing fails, show raw text.

- [ ] **Step 3: Build frontend**

Run:

```powershell
cd frontend
npm run build
```

Expected: build succeeds.

## Task 5: Write User-Facing Documentation

**Files:**
- Create: `docs/违规停车判定算法优化说明.md`
- Modify: `README.md`

- [ ] **Step 1: Write Chinese explanation document**

Include:

- 为什么原来的单帧判断显得简单。
- ROI overlap 是什么。
- IoU tracking 是什么。
- dwell frames 为什么能过滤经过车辆。
- 每个文件的作用。
- 如何运行图片测试和视频测试。
- 如何在前端查看判定依据。
- 简历 bullet 和面试讲法。

- [ ] **Step 2: Link from README**

Add a short section under project overview or docs section pointing to the new document.

## Task 6: Final Verification

**Files:**
- All modified files.

- [ ] **Step 1: Run Python tests**

```powershell
cd vision
python -m pytest test_decision_logic.py -q
```

- [ ] **Step 2: Run backend build**

```powershell
cd backend
mvn -q -DskipTests package
```

- [ ] **Step 3: Run frontend build**

```powershell
cd frontend
npm run build
```

- [ ] **Step 4: Check git diff**

```powershell
git diff --stat
git diff --check
```

Expected: no whitespace errors.
