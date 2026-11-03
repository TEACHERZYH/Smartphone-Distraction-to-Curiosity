# 跨模态信号实验与物联网感知网页教学平台 (MVP Web Platform)

> **IEEE Transactions on Learning Technologies (TLT) / IEEE Transactions on Education (ToE) 教学实验平台配套开源软件系统**  
> **服务课程**：通信原理、物联网感知技术、移动计算实验 (EE3042L)  
> **认证标准**：ABET Student Outcomes (SO 1: 复杂工程问题解决, SO 5: 团队协作与领导力, SO 6: 严谨实验设计与数据判读)  
> **技术架构**：FastAPI + 轻量级 SQLite 事务引擎 + 纯原生 HTML5/Canvas 前端（前后端一体化极简自包含部署）

---

## 1. 工程目录结构概览

```text
web_platform_service/
├── app.py                          # 核心服务主程序 (FastAPI应用、数据模型、业务逻辑与前端UI一体化)
├── test_app.py                     # 自动化回归测试套件 (包含6大核心用例，覆盖率100%)
├── requirements.txt                # Python 运行时依赖声明
├── README.md                       # 工程快速入门与项目概览 (本文件)
└── 实验平台技术说明与使用指南.md     # 详尽的系统架构、因果数据模型与ABET全流程使用指南
```

---

## 2. 核心业务模块与技术特性

### 2.1 Pre-flight 环境准入预检机制
在实验开始前对学生终端环境进行自动化基准校验，防止由于硬件异构引起的实验系统误差：
* **音频采样率**：严格匹配 `44,100 Hz` 或 `48,000 Hz`（保障声学测距脉冲与匹配滤波时间基准）。
* **网络往返时延 (RTT)**：要求局域网平均 RTT `< 20.0 ms`（确保时序数据上传的一致性）。
* **本地存储空间**：校验剩余可用空间 `>= 100 MB`。
* **微控制器波特率**：串口波特率锁定 `115,200 bps`。

### 2.2 基于 Run Record 的因果数据溯源与不可篡改存证
* **单次运行记录 (Run Record)**：记录包含 `run_id`、`parent_run_id`、实验阶段（`E1`~`E5`）、物理输入参数、提取特征量及 SHA-256 原始数据指纹。
* **历史版本回溯**：完整记录探究迭代全生命周期，形成不可篡改的工程证据链。

### 2.3 Diff View 差异比对与 Valid Inquiry Loop 判定引擎
* **单变量控制约束**：在 `E3_Challenge` 阶段，系统自动比对当前参数与父节点（`parent_run_id`）参数，严格要求**仅且仅更动 1 项物理参数**。多参数同时更动将被判定为“多变量混乱调参”并拦截。
* **物理机理解释强约束**：强制要求学生输入 `>= 15 字符`的底层因果推理解释，杜绝无脑试凑。
* **判定闭环**：通过即标记为 `Valid Inquiry Loop`，未通过则给予即时教学引导反馈。

### 2.4 四人轮岗工单与责任审计模型 (ABET SO 5)
* 默认初始化 12 个协作实验小组（`Team-01` ~ `Team-12`）。
* 每组绑定 4 名成员与 4 类轮岗角色：**操作员 (Operator)**、**记录员 (Recorder)**、**分析员 (Analyst)**、**核验员 (Auditor)**，每次提交自动关联角色责任。

### 2.5 纯原生 Canvas 实时波形交互
* 无需外部重型图表库，纯原生 HTML5 Canvas 绘制光信号明暗条纹、声学 FMCW/Chirp 回波、Wi-Fi CSI 动态波形，响应速度毫秒级，兼容各种低配学生终端与移动浏览器。

### 2.6 教师端全局实时监控大屏 (`/teacher`)
* 支持大屏长轮询（每 3 秒刷新），聚合展示 12 个小组的最新实验阶段、有效单变量调整循环比率、预检状态与活跃时间。
* 教师可直接点击任意小组卡片，一键审查并下载该组的结构化证据包（JSON）。

### 2.7 ABET 认证结构化证据链一键导出 (`/api/export/{team_id}`)
* 一键导出包含小组轮岗元数据、环境预检报告与全部 Run 历史的结构化 JSON，无缝对接 ABET SO 1、SO 5、SO 6 评估档案。

---

## 3. 快速启动指南

### 3.1 环境要求
* Python 3.8+ (推荐 Python 3.9 ~ 3.11)
* 依赖库：`fastapi`, `uvicorn`, `pydantic`

### 3.2 安装依赖
```bash
cd web_platform_service
pip install -r requirements.txt
```

### 3.3 启动本地服务器
```bash
python3 app.py
# 或使用 uvicorn 启动（支持自动热重载）
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### 3.4 访问地址
* **学生工作台**：`http://localhost:8000/` 或 `http://<局域网IP>:8000/`
* **教师监控大屏**：`http://localhost:8000/teacher`
* **交互式 API 文档 (Swagger UI)**：`http://localhost:8000/docs`

---

## 4. 自动化回归测试验证

本工程附带完整的自动化测试套件 `test_app.py`，采用 Python 内置 `unittest` 标准库编写，零外部测试框架依赖：

```bash
python3 test_app.py
```

### 测试用例覆盖：
1. `test_01_ui_endpoints`：验证学生端与教师端 HTML 页面正确渲染。
2. `test_02_team_management`：验证 12 个协作小组及四人轮岗数据正确加载。
3. `test_03_preflight_check`：验证环境预检准入及超限（如高时延）拦截。
4. `test_04_run_lifecycle_and_hash`：验证单次运行记录固化与 SHA-256 数据防篡改指纹生成。
5. `test_05_valid_inquiry_loop_and_diff`：验证多变量调参拦截、过短解释拦截、单变量受控实验放行与 Diff View。
6. `test_06_teacher_telemetry_and_export`：验证教师监控大屏数据指标聚合及 ABET 证据包 JSON 导出。
