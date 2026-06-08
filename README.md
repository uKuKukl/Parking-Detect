# 校园违规停车报告生成系统

本项目是一个面向校园电动车违规停放管理场景的综合系统，结合 YOLO 目标检测、大语言模型通报生成、Spring Boot 后端和 Vue 3 前端，实现从图像检测、违规复核、报告生成到数据看板展示的完整流程。

## 项目概述

系统以校园非机动车停放治理为应用背景，主要完成以下工作：

- 使用 YOLO 模型识别图像中的电动车/摩托车目标。
- 支持电子围栏 ROI 规则，用于判断车辆是否处于违规停放区域。
- 将检测结果推送到后端，形成待复核违规记录。
- 提供后台管理页面，支持人工复核、设备管理、围栏配置和审核日志查看。
- 调用 OpenAI 兼容格式的大语言模型接口，为确认违规记录生成通报文本。
- 支持违规数据统计、趋势分析、报告展示和 Word/Excel 导出。
- 支持将视觉检测模块服务化为 FastAPI 推理服务，后端优先通过 HTTP 调用常驻模型，服务不可用时回退到原 Python 脚本。
- 提供 Docker Compose、Actuator 健康检查和 GitHub Actions CI，便于一键部署和持续验证。

新增的算法优化说明见：

```text
docs/违规停车判定算法优化说明.md
```

该文档说明了如何通过 ROI 面积重叠、IoU 轻量目标跟踪和连续帧滞留阈值，减少边缘误检和短暂经过车辆造成的误报。

模型训练与评估闭环说明见：

```text
docs/model_training_evaluation.md
```

该文档说明了如何通过训练脚本、评估脚本和实验报告，把 YOLO 模型迭代过程转化为可复现、可量化、可写进简历的实验材料。

## 技术栈

| 模块 | 技术 |
| --- | --- |
| 后端 | Java 17、Spring Boot 3.2、MyBatis-Plus、MySQL、LangChain4j、Apache POI |
| 前端 | Vue 3、Vite、Element Plus、Vue Router、Pinia、Axios |
| 视觉检测 | Python、FastAPI、Ultralytics YOLO、OpenCV、NumPy、Requests |
| 数据库 | MySQL 8.0 |
| 大模型接口 | OpenAI 兼容 API |
| 工程化 | Docker Compose、Spring Boot Actuator、GitHub Actions |

## 目录结构

```text
Parking-Detect/
├── backend/                 # Spring Boot 后端
│   ├── db/                  # 数据库初始化脚本
│   ├── src/main/java/       # 后端业务源码
│   ├── src/main/resources/  # 后端配置文件
│   ├── pom.xml              # Maven 配置
│   └── prompt_template.txt  # 通报生成提示词模板
├── frontend/                # Vue 3 前端管理台
│   ├── src/
│   ├── package.json
│   └── vite.config.js
├── vision/                  # YOLO 视觉检测模块
│   ├── models/best.pt       # 检测模型权重
│   ├── vision.py            # 检测与推送脚本
│   ├── train_yolo.py        # 模型训练与实验 manifest 生成
│   ├── eval_metrics.py      # 模型 Precision/Recall/mAP/延迟评估
│   ├── experiment_report.py # 实验报告汇总脚本
│   └── requirements.txt
├── vision-service/          # FastAPI 常驻推理服务
│   ├── app/
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── docker-compose.yml       # MySQL + 后端 + 前端 + 视觉服务一键启动
├── .github/workflows/ci.yml # Maven、前端、Python 测试流水线
├── docs/                    # 论文、答辩和流程说明材料
├── for test/                # 测试图片
├── work_doc/                # 论文相关文档与图表
└── prompts.md               # 提示词记录
```

## 环境要求

- JDK 17 或以上
- Maven 3.6 或以上
- MySQL 8.0
- Node.js 16 或以上，推荐 18/20
- Python 3.8 或以上

## 运行配置

后端配置文件位于：

```text
backend/src/main/resources/application.yml
```

推荐通过环境变量配置本地密码和大模型接口信息：

```powershell
$env:DB_PASSWORD="你的 MySQL root 密码"
$env:LLM_API_KEY="你的大模型 API Key"
$env:LLM_BASE_URL="https://api.openai.com/v1"
$env:LLM_MODEL_NAME="gpt-4o-mini"
$env:VISION_SERVICE_BASE_URL="http://127.0.0.1:8001"
```

如果使用其他 OpenAI 兼容服务，只需要把 `LLM_BASE_URL` 和 `LLM_MODEL_NAME` 改成对应服务的地址和模型名称。

后端健康检查接口：

```text
http://127.0.0.1:8080/actuator/health
http://127.0.0.1:8080/actuator/metrics
```

## 数据库初始化

1. 确认 MySQL 服务已经启动。
2. 使用 MySQL 客户端执行初始化脚本：

```powershell
mysql -uroot -p < backend/db/schema.sql
```

脚本会创建数据库 `parking_detect`，并初始化系统用户、违规记录、摄像头设备、电子围栏和审核日志等数据表。

默认账号：

| 角色 | 用户名 | 密码 |
| --- | --- | --- |
| 管理员 | `admin` | `admin123` |
| 审核员 | `auditor` | `auditor123` |

## 启动后端

进入后端目录并启动 Spring Boot：

```powershell
cd backend
mvn spring-boot:run
```

后端默认监听：

```text
http://127.0.0.1:8080
```

如果控制台出现 Tomcat started on port 8080，说明后端启动成功。

## 启动前端

进入前端目录，安装依赖并启动开发服务器：

```powershell
cd frontend
npm install
npm run dev
```

前端默认访问地址：

```text
http://127.0.0.1:5173
```

如果开启了代理或 TUN 模式，建议优先使用 `127.0.0.1` 访问，避免 `localhost` 被代理规则影响。

## 启动视觉检测模块

视觉检测有两种运行方式。推荐开发和简历展示时使用服务化模式；只想保留原始联调路线时仍可使用脚本模式。

### 服务化模式

进入视觉模块目录，创建并激活虚拟环境：

```powershell
cd vision-service
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

启动 FastAPI 推理服务：

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

服务默认会加载：

```text
vision/models/best.pt
```

健康检查和运行指标：

```text
http://127.0.0.1:8001/health
http://127.0.0.1:8001/metrics
```

后端 `/api/violations/upload-image` 会优先调用 `vision-service /detect`，返回检测结果后直接落库；如果服务不可用，会自动回退到原来的 `vision/vision.py` 脚本路径。

### 脚本模式

进入 `vision` 目录，创建并激活虚拟环境：

```powershell
cd vision
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

确保后端已经启动后，可以使用测试图片运行检测：

```powershell
python vision.py --source "..\for test\North.jpg"
```

常用参数：

| 参数 | 说明 |
| --- | --- |
| `--source` | 输入图片路径，默认 `test_image.jpg` |
| `--roi` | 电子围栏 ROI JSON，由后端上传检测流程自动传入 |
| `--camera-id` | 摄像头编号 |
| `--conf` | 临时覆盖置信度阈值，例如 `--conf 0.5` |

检测成功后，脚本会将结果推送到：

```text
http://127.0.0.1:8080/api/violations/upload
```

并在后台系统中生成待复核记录。

## Docker Compose 一键启动

确认 Docker Desktop 已启动后，在项目根目录执行：

```powershell
docker compose up --build
```

默认端口：

| 服务 | 地址 |
| --- | --- |
| 前端 | `http://127.0.0.1:5173` |
| 后端 | `http://127.0.0.1:8080` |
| 后端健康检查 | `http://127.0.0.1:8080/actuator/health` |
| 视觉服务 | `http://127.0.0.1:8001` |
| 视觉服务健康检查 | `http://127.0.0.1:8001/health` |
| MySQL | `127.0.0.1:3306` |

停止服务：

```powershell
docker compose down
```

如需清空数据库卷：

```powershell
docker compose down -v
```

## CI 验证

仓库已提供 GitHub Actions 配置：

```text
.github/workflows/ci.yml
```

流水线包含：

- 后端 `mvn -B -DskipTests package`
- 前端 `npm ci && npm run build`
- Python 视觉模块单元测试
- FastAPI `vision-service` 辅助逻辑测试

## 模型训练与评估闭环

如果需要把项目升级为更适合简历展示的版本，可以补充真实数据集后运行以下流程。

训练模型：

```powershell
cd vision
python train_yolo.py --data "D:\datasets\parking\data.yaml" --model yolov8n.pt --epochs 50 --imgsz 960 --batch 8 --device 0 --name parking_yolov8n_img960
```

只检查配置、不实际训练：

```powershell
python train_yolo.py --data "D:\datasets\parking\data.yaml" --dry-run
```

评估指标：

```powershell
python eval_metrics.py --model ".\output\training\parking_yolov8n_img960\weights\best.pt" --data "D:\datasets\parking\data.yaml" --split test --imgsz 960 --batch 8 --device 0 --run-name parking_yolov8n_img960_test
```

生成实验报告：

```powershell
python experiment_report.py
```

报告默认输出到：

```text
vision/output/experiment_report.md
```

## 页面说明

| 路径 | 功能 |
| --- | --- |
| `/login` | 用户登录 |
| `/dashboard` | 数据看板和统计分析 |
| `/audit` | 违规记录复核、图片查看、上传检测 |
| `/report` | 通报生成、报告展示、Word/Excel 导出 |
| `/cameras` | 摄像头设备管理 |
| `/roi` | 电子围栏 ROI 配置 |
| `/logs` | 审核日志查看 |
| `/settings` | 通报生成提示词配置 |

普通审核员可以访问看板、复核台和报告页面；管理员可以访问设备、围栏、日志和系统设置页面。

## 推荐演示流程

1. 启动 MySQL，并执行 `backend/db/schema.sql`。
2. 启动 `vision-service`，或使用 Docker Compose 一键启动全套服务。
3. 启动后端服务。
4. 启动前端管理台。
5. 使用 `admin / admin123` 登录系统。
6. 在 `/roi` 配置电子围栏，或直接在 `/audit` 上传测试图片触发检测。
7. 在 `/audit` 查看待复核记录，并确认违规或驳回误报。
8. 在 `/report` 点击生成通报，查看大模型生成的违规停车通报文本。
9. 在 `/dashboard` 查看统计数据和趋势分析。

## 常见问题

### 1. 后端启动失败，提示数据库连接错误

检查 MySQL 是否启动、`parking_detect` 数据库是否已创建，以及 `DB_PASSWORD` 是否与本机 MySQL 密码一致。

### 2. 前端能打开，但接口请求失败

确认后端是否运行在 `8080` 端口。若开启代理或 TUN 模式，建议使用 `http://127.0.0.1:5173` 访问前端。

### 3. 视觉检测脚本无法加载模型

确认 `vision/models/best.pt` 是否存在。如果模型文件不在该目录，需要修改 `vision.py` 中的 `MODEL_PATH`。

### 4. 无法生成通报文本

确认 `LLM_API_KEY`、`LLM_BASE_URL` 和 `LLM_MODEL_NAME` 配置正确，并且当前网络可以访问对应大模型服务。

## 论文研究方向

本项目主要属于计算机视觉方向，具体聚焦于基于深度学习的目标检测技术在校园违规停车识别中的应用，并结合大语言模型实现检测结果的自动通报生成。
