# 视觉检测 (Python YOLOv8) 运行指南

本文档指导您如何配置独立 Python 虚拟环境并运行 `vision.py`，实现真实的 YOLOv8 目标检测，并将违规数据推送给 Spring Boot 后端。

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
