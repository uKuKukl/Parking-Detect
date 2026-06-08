# YOLO 模型训练与评估闭环说明

## 1. 优化目标

原项目已经能完成 YOLO 检测、ROI 违规判定、人工复核和报告生成。为了让项目更适合写进简历，需要补齐模型实验闭环：

```text
数据集 data.yaml
  -> 训练脚本 train_yolo.py
  -> 评估脚本 eval_metrics.py
  -> 实验报告 experiment_report.py
  -> README / 简历 / 面试材料
```

这样面试时不只说“用了 YOLO”，还能说明模型如何训练、如何评估、哪些参数做过对比、指标如何记录。

## 2. 新增能力

### 2.1 可复现实验训练

入口文件：

```text
vision/train_yolo.py
```

示例命令：

```powershell
cd "D:\Program Files\Parking-Detect\vision"
.\venv\Scripts\python.exe train_yolo.py `
  --data "D:\datasets\parking\data.yaml" `
  --model yolov8n.pt `
  --epochs 50 `
  --imgsz 960 `
  --batch 8 `
  --device 0 `
  --name parking_yolov8n_img960
```

训练输出会保存到：

```text
vision/output/training/
```

其中 `*_manifest.json` 会记录模型、数据集、epoch、图片尺寸、batch、device、seed、notes 和权重路径，方便复盘。

如果只是检查配置，不想真正训练，可以运行：

```powershell
.\venv\Scripts\python.exe train_yolo.py --data "D:\datasets\parking\data.yaml" --dry-run
```

### 2.2 指标评估

入口文件：

```text
vision/eval_metrics.py
```

示例命令：

```powershell
.\venv\Scripts\python.exe eval_metrics.py `
  --model ".\output\training\parking_yolov8n_img960\weights\best.pt" `
  --data "D:\datasets\parking\data.yaml" `
  --split test `
  --imgsz 960 `
  --batch 8 `
  --device 0 `
  --run-name parking_yolov8n_img960_test `
  --notes "YOLOv8n, imgsz=960, test split"
```

评估输出会保存到：

```text
vision/output/metrics/
```

JSON 中包含：

- Precision
- Recall
- mAP@0.5
- mAP@0.5:0.95
- 预处理、推理、后处理耗时
- 平均单张延迟
- 模型、数据集、split、imgsz、batch、device、notes

### 2.3 实验报告生成

入口文件：

```text
vision/experiment_report.py
```

示例命令：

```powershell
.\venv\Scripts\python.exe experiment_report.py
```

生成结果：

```text
vision/output/experiment_report.md
```

报告会汇总训练配置、评估指标，并自动给出简历表达建议。评估记录会按 `mAP@0.5:0.95` 从高到低排序。

## 3. 建议实验设计

第一轮不用做太复杂，建议只做 3 组：

| 实验 | 模型 | imgsz | 目标 |
| --- | --- | ---: | --- |
| baseline | YOLOv8n | 640 | 建立最低成本基线 |
| high-res | YOLOv8n | 960 | 验证小目标和远距离车辆是否改善 |
| larger-model | YOLOv8s | 960 | 验证更大模型是否带来明显 mAP 提升 |

每组记录：

- 训练耗时
- 最佳 epoch
- Precision / Recall / mAP@0.5 / mAP@0.5:0.95
- 单张推理耗时
- 典型误检和漏检截图

## 4. 面试讲法

可以这样讲：

> 我没有只停留在调用 YOLO 做检测，而是补了一套训练和评估闭环。训练脚本会固定模型、数据集、epoch、imgsz、batch、device 和 seed，并把实验参数写入 manifest；评估脚本统一输出 Precision、Recall、mAP@0.5、mAP@0.5:0.95 和推理延迟；最后通过报告脚本把多次实验汇总成 Markdown，按 mAP@0.5:0.95 排序，方便比较不同模型和输入尺寸的取舍。

简历可以写：

```text
- 搭建 YOLOv8 模型训练与评估流水线，统一记录训练参数、Precision、Recall、mAP@0.5、mAP@0.5:0.95 和推理延迟，并生成实验对比报告，支撑模型选型和误检分析。
```
