# Role & Context
你现在是一个资深的全栈 AI 工程师。你需要协助我完成一个名为《基于 YOLO 识别与 LLM 的校园违规停车报告生成系统》的本科毕业设计项目。

【强制执行规则】：请严格按照以下步骤，逐个模块完成代码编写。在输出完当前 Step 的代码和说明后，**必须停止生成**，并向我询问：“当前步骤已完成，请在本地测试。测试通过后请回复‘继续’，我将开始下一步。” 绝对不要一次性生成多个步骤的代码。

# Tech Stack & Environment
- **运行环境**: 纯本地运行 (localhost)。
- **视觉检测**: 必须使用独立的 Python 虚拟环境 (venv)，编写单独的 `vision.py` 脚本，加载真实的本地 YOLOv8 `.pt` 模型进行推理，**严禁使用任何模拟(mock)数据**。
- **后端服务**: Spring Boot 3.x (Java 17+), MyBatis-Plus
- **数据库**: 本地已安装的 MySQL 8.0 (不使用 docker-compose)。
- **LLM 编排**: 直接在 Spring Boot 中集成 LangChain4j。
- **大模型 API**: 优先适配 Gemini API 或 xAI API，API Key 必须通过 application.yml 或环境变量读取，严禁硬编码。
- **前端页面**: Vue 3 (Composition API) + Element Plus + Vite + Pinia

---

# Execution Steps (分步执行清单)

## Step 1: 数据库与实体类设计 (MySQL + Spring Boot)
1. 设计核心表 `parking_violations` 的 SQL 脚本。字段包含：`id`, `detect_time`, `location`, `image_path` (存储本地绝对或相对路径), `camera_id`, `confidence`, `status` (0-待复核, 1-已确认, 2-已驳回, 3-已生成报告)。
2. 提供 Spring Boot 的 `application.yml` 配置（包含本地 MySQL 数据库连接与大模型 API Key 占位符）。
3. 生成对应的 Entity, Mapper, Service 和 Controller 骨架代码。

## Step 2: 真实视觉检测与数据推送 (Python -> Spring Boot)
1. 提供 Python 独立虚拟环境的创建指南，并输出 `requirements.txt`（包含 `ultralytics`, `opencv-python`, `requests` 等运行 YOLOv8 所需的真实依赖）。
2. 编写独立的 `vision.py` 脚本。该脚本需加载本地的 `.pt` 模型，对测试图片或视频流进行真实的目标检测。
3. 在 `vision.py` 中实现逻辑：当检测到违规目标并超过置信度阈值时，保存带有边界框的截图，并将识别结果（时间、地点、截图路径、摄像头ID、置信度等）组装成 JSON payload。
4. 在 Spring Boot 中实现 POST 接口 `/api/violations/upload`，接收上述 JSON 数据并写入数据库。`vision.py` 需通过 HTTP 请求将真实推理数据推送到该后端接口。

## Step 3: LLM 报告生成引擎 (LangChain4j)
1. 在 Spring Boot 项目中引入 `langchain4j` 相关依赖，并配置大模型客户端。
2. 编写一个服务类，读取数据库中 `status=1` (已确认) 的违规记录。
3. 设计 Prompt Template：“请根据以下信息，生成一份正式、简洁的校园安全通报：时间：{{time}}，地点：{{location}}，设备：{{camera_id}}，发现电动车违规停放。要求包含事件描述、安全隐患说明、整改建议。”
4. 调用大模型生成文本，将生成的报告文本存入数据库，并将该记录的 `status` 更新为 3。

## Step 4: 后台管理前端开发 (Vue3 + Element Plus)
提供基础的前端路由和三个核心页面组件代码：
1. **违规复核台 (`AuditView.vue`)**: 表格展示 `status=0` 的记录。提供“确认违规”(status->1) 和“误报驳回”(status->2) 操作，调用后端接口。
2. **报告展示看板 (`ReportView.vue`)**: 以卡片形式展示已生成的违规通报文本 (status=3)，提供“一键复制到剪贴板”功能。
3. **系统设置 (`SettingsView.vue`)**: 表单页面，用于动态修改并保存 LLM 的 Prompt 模板内容。

## Step 5: 本地运行与联调指南
输出一份简洁的 Markdown 指南，说明：
1. 后端 Spring Boot 如何配置运行以及执行 SQL 脚本。
2. 前端依赖如何安装及启动。
3. Python 虚拟环境如何激活以及 `vision.py` 如何运行以触发完整流程。