# 校园违规停车报告生成系统 - 本地运行联调指南

这是一个综合了计算机视觉 (YOLOv8)、大语言模型 (LLM)、Spring Boot 后端和 Vue 3 前端的完整项目联调指南。请严格按以下顺序进行配置和运行。

---

## 模块 1：后端服务 (Spring Boot) 与数据库结构

1. **环境要求**: Java 17+, MySQL 8.0, Maven 3.6+
2. **初始化数据库**:
   * 打开您的 MySQL 客户端 (如 Navicat 或 DataGrip)。
   * 执行 `backend/db/schema.sql` 脚本，这会自动创建数据库 `parking_detect` 及数据表 `parking_violations`。
3. **修改配置文件**:
   * 打开 `backend/src/main/resources/application.yml`。
   * 修改 `spring.datasource.password` 为您的本地 MySQL 密码。
   * 修改 `llm.api-key` 为您的真实 Gemini 或 xAI 等兼容 OpenAI 格式的大模型 API Key。
   * 修改 `llm.base-url` 代理地址（如果是 xAI 则改为 `https://api.x.ai/v1` 等，按实际填写）。
   * 修改 `llm.model-name`（例如 `gpt-3.5-turbo`, `gemini-pro`, `grok-1` 等）。
4. **启动项目**:
   * **方法 A (VSCode / 命令行)**: 在 VSCode 终端中，切换到 `backend` 目录，运行 `mvn spring-boot:run` 即可启动。
   * **方法 B (IDEA 等 IDE)**: 导入 `backend` 为 Maven 项目，运行 `ParkingDetectApplication` 主类。
   * 确保控制台输出 `Tomcat started on port 8080` 无报错。

---

## 模块 2：视觉检测引擎 (Python + YOLOv8)

1. **环境要求**: Python 3.8 或以上
2. **创建并进入虚拟环境**：
   * 打开终端进入 `vision` 目录：`cd vision`
   * 创建虚拟环境：`python -m venv venv`
   * 激活环境：
     * Windows: `.\venv\Scripts\activate`
     * macOS/Linux: `source venv/bin/activate`
3. **安装依赖**:
   * 在激活的虚拟环境中执行：`pip install -r requirements.txt`
4. **运行测试**:
   * 请确保后端 Sprint Boot（8080端口）已启动！
   * 在 `vision` 目录放入一张测试图片 `test_image.jpg`（或者修改 `vision.py` 中的 `test_source = 0` 调用摄像头）。
   * 终端中运行：`python vision.py`
   * 成功的话终端会提示：`[SUCCESS] 数据成功推送到 Spring Boot 后端！`

---

## 模块 3：前端管理台 (Vue 3 + Element Plus)

1. **环境要求**: Node.js 16+ (推荐 18 或 20)
2. **安装依赖**:
   * 打开终端进入 `frontend` 目录：`cd frontend`
   * 运行：`npm install`
3. **启动前端开发服务器**:
   * 运行：`npm run dev`
   * 打开浏览器访问终端输出的本地地址（通常是 `http://localhost:5173`）。
4. **主要功能页面使用流程**:
   * **违规复核台 (/audit)**: 可以看到刚才 Python 脚本推送的数据（状态为“待复核”）。点击“确认违规”修改状态。
   * **系统设置 (/settings)**: 可查看并修改 LLM 的生成 prompt 模板，支持修改后自动保存。
   * **报告展示看板 (/report)**: 点击**“生成通报”**按钮，前端会请求后端的大模型接口，为**已确认为违规**的数据生成报告文本。生成完毕后再点“刷新”即可看到卡片报告及“一键复制”功能。

---

> **🎉 至此，毕业设计《基于 YOLO 识别与 LLM 的校园违规停车报告生成系统》的所有功能模块均已联通测试完毕！祝顺利通过答辩！**
