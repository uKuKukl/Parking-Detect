# ROI + IoU 跟踪滞留判定设计

## 背景

当前 `vision/vision.py` 已经能调用 YOLO 模型检测车辆，并根据电子围栏 ROI 判断是否需要上报后端。现有逻辑主要依赖单帧结果和一个代表车辆接地点的点位判断，技术链路较直接，容易出现以下问题：

- 车辆框只擦到 ROI 边缘时，单点判断可能把临时经过或边缘目标误判为有效停放。
- 单张图或单帧检测没有时间维度，无法区分“路过车辆”和“实际停留车辆”。
- 后端只保存最终状态，缺少算法判定依据，面试时不容易解释为什么这条记录被判定为违规。

## 目标

新增一个可解释的违规停车判定闭环：在 YOLO 检测结果之后，引入 ROI 几何重叠比例、IoU 目标关联和连续帧滞留阈值，再把判定依据保存到后端并在前端复核台展示。

## 核心设计

### 1. ROI 几何重叠比例

将电子围栏继续视为“允许停放区”。对每个 YOLO bbox 计算：

```text
legal_overlap_ratio = bbox 与合法 ROI 的重叠面积 / bbox 面积
```

当 `legal_overlap_ratio >= roi_overlap_threshold` 时，认为目标主要位于允许停放区内；否则认为它是违规候选。默认阈值建议为 `0.35`，含义是至少 35% 的目标框需要落在合法区域内，才算“停在允许区域”。

### 2. IoU 轻量目标跟踪

在连续帧中使用 bbox IoU 做贪心匹配：

```text
IoU = 两个 bbox 的交集面积 / 并集面积
```

当新检测框与上一帧某个 track 的 IoU 大于 `track_iou_threshold`，复用该 track id；否则新建 track。默认阈值为 `0.30`。这不是完整 ByteTrack，但足够支撑本项目的轻量场景，并且代码可读、面试可解释。

### 3. 滞留帧阈值

每个 track 只有在连续多帧都处于违规候选状态时，才升级为“确认违规”：

```text
dwell_frames >= dwell_frame_threshold
```

单张图片默认阈值为 `1`，保持现有上传图片流程可用；视频流或摄像头输入默认阈值为 `3`，用于过滤短暂经过目标。用户也可以通过命令行显式传入 `--dwell-frames`。

### 4. 判定依据落库与展示

后端 `parking_violations` 增加 `decision_details` 字段，保存 JSON 字符串，内容包括：

- 算法名称。
- ROI 重叠阈值、IoU 阈值、滞留帧阈值。
- 处理帧数、总检测数、确认违规数。
- 每个 track 的 `trackId`、最大置信度、最大滞留帧数、合法区域重叠比例和判定原因。

前端复核台新增“判定依据”入口，方便查看该记录的算法解释。

## 文件边界

- `vision/decision_logic.py`：新增。只放几何重叠、IoU、轻量跟踪和详情 JSON 组装逻辑，不依赖 YOLO。
- `vision/vision.py`：修改。继续负责模型推理、图片标注、调用判定模块、向后端上报。
- `vision/test_decision_logic.py`：新增。覆盖 IoU、ROI 重叠、滞留阈值等核心逻辑。
- `backend/db/schema.sql`、`backend/db/rebuild.sql`：增加 `decision_details` 字段。
- `backend/src/main/java/com/parking/detect/entity/ParkingViolation.java`：增加 `decisionDetails` 属性。
- `backend/src/main/java/com/parking/detect/controller/ParkingViolationController.java`：导出时补充判定依据。
- `frontend/src/views/AuditView.vue`：复核台新增判定依据查看弹窗。
- `docs/违规停车判定算法优化说明.md`：面向用户的详细中文说明文档。

## 错误处理

- ROI 解析失败时继续降级为全图禁停模式，但在控制台打印错误。
- ROI 参考尺寸非法时退出，避免错误比例导致误判。
- 如果没有合法 ROI，则所有检测框都进入违规候选，再由滞留阈值判断。
- 如果判定详情为空，前端展示“暂无判定详情”，不影响旧数据浏览。

## 验收标准

- `vision/decision_logic.py` 的核心函数有单元测试。
- 单张图片仍可通过 `vision.py --source <image>` 上报。
- 带 ROI 时，bbox 与合法区域重叠比例会影响违规候选判断。
- 带多帧输入时，同一目标需要满足滞留帧阈值才会被确认。
- 后端实体和数据库脚本包含 `decision_details` 字段。
- 前端复核台可以查看算法判定依据。
- 文档能用中文解释清楚算法原理、运行方式、代码位置和简历写法。
