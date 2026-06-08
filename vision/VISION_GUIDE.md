# 视觉检测 (Python YOLOv8) 运行指南

本文档指导您如何配置独立 Python 虚拟环境并运行 `vision.py`，实现真实的 YOLOv8 目标检测，并将违规数据推送给 Spring Boot 后端。

当前项目同时支持两种视觉运行方式：

- `vision.py` 脚本模式：适合单次调试和保留原毕业设计演示流程。
- `vision-service` 服务化模式：适合长期运行、后端上传图片联调和简历展示，模型在服务启动时加载一次。

## 1. 创建 Python 虚拟环境 (venv)

请打开 Terminal (PowerShell 或 Cmd)，进入到 `vision` 目录：

```bash
cd "d:\Program Files\Parking-Detect\vision"

# 创建名为 venv 的虚拟环境
python -m venv venv

# 激活虚拟环境 (Windows)
.\venv\Scripts\activate
```

*(激活成功后，命令行前缀应该会显示 `(venv)`)*

## 2. 安装依赖包

在**已激活的虚拟环境**中执行：

```bash
pip install -r requirements.txt
```

*(这会自动安装 ultralytics, opencv-python, requests 等真实运行所需的依赖)*

## 3. 准备测试资源

为了能触发真实的“违规检测”，您需要一张测试图片。
1. 找一张有“电动车/摩托车”或者“自行车”的图片，放入 `vision` 目录下，并命名为 `test_image.jpg`。
2. （可选）如果您有摄像头，您可以直接编辑 `vision.py` 第 26 行左右的代码，将 `test_source = "test_image.jpg"` 改为 `test_source = 0`。

## 4. 运行推理与数据推送

**极其重要：** 在运行之前，必须确保**后端 Spring Boot 项目已启动**（在端口 8080 监听），并且数据库中已连接正常。

运行脚本：
```bash
python vision.py
```

### 预期结果:
1. 脚本将自动下载 YOLO 权重文件（第一次运行）。
2. 调用 YOLO 模型推理，检测出违规车辆目标（`confidence > 0.5`）。
3. 生成带有边界框的实景截图，保存在 `vision/output/` 目录下。
4. 终端日志显示 `[SUCCESS] 数据成功推送到 Spring Boot 后端！`。
5. 此时您去 MySQL 的 `parking_violations` 表中查看，将会看到一条新增的数据！

## 5. 运行 FastAPI 视觉服务

在项目根目录进入 `vision-service`：

```bash
cd "d:\Program Files\Parking-Detect\vision-service"
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

启动服务：

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

健康检查：

```text
http://127.0.0.1:8001/health
```

运行指标：

```text
http://127.0.0.1:8001/metrics
```

后端的 `/api/violations/upload-image` 会优先调用该服务的 `/detect` 接口，返回 `location`、`imagePath`、`cameraId`、`confidence`、`decisionDetails` 等字段并保存到数据库。如果该服务未启动，后端会回退到 `vision.py` 脚本执行路径。

## 6. 训练和评估模型

如果你已经准备好 YOLO 格式的数据集，并且有 `data.yaml`，可以用下面的命令建立模型实验闭环。

### 6.1 训练

```bash
python train_yolo.py --data "D:\datasets\parking\data.yaml" --model yolov8n.pt --epochs 50 --imgsz 960 --batch 8 --device 0 --name parking_yolov8n_img960
```

训练脚本会在 `vision/output/training/` 下保存训练结果和 `*_manifest.json`，用于记录本次实验的模型、数据集、epoch、图片尺寸、batch、device 和备注。

只想检查数据集路径和参数时，可以运行：

```bash
python train_yolo.py --data "D:\datasets\parking\data.yaml" --dry-run
```

### 6.2 评估

```bash
python eval_metrics.py --model ".\output\training\parking_yolov8n_img960\weights\best.pt" --data "D:\datasets\parking\data.yaml" --split test --imgsz 960 --batch 8 --device 0 --run-name parking_yolov8n_img960_test
```

评估脚本会输出 Precision、Recall、mAP@0.5、mAP@0.5:0.95 和平均单张延迟，并把 JSON 指标保存到 `vision/output/metrics/`。

### 6.3 生成实验报告

```bash
python experiment_report.py
```

报告默认生成到：

```text
vision/output/experiment_report.md
```

这份报告可以直接用于 README、答辩材料和简历项目描述。
