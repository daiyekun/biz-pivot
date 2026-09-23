# 商枢 BizPivot 企业智能AI平台 —— 第一阶段测试报告

## 文档基础信息

| 项目名称 | 商枢 BizPivot 企业智能AI平台 |
| -------- | ---------------------------- |
| 文档名称 | 第一阶段测试报告（biz-pivot_test-report） |
| 测试范围 | 开发计划《development_plan.md》**阶段一：项目架构与基础底座搭建** |
| 测试依据 | `docs/development_plan.md`、`docs/database_design.md`、`docs/project_structure.md`、`docs/biz_pivot_prd.md` |
| 测试方式 | 静态代码审查 + 运行时冒烟测试（不修改任何代码） |
| 测试环境 | Windows + Python 3.13（.venv）+ Node v24.14.0 + Docker 依赖服务（PG15/Redis7.2/Qdrant/RabbitMQ3.13/Jaeger 均 Up） |
| 测试日期 | 2026-09-23 |
| 测试结论 | **阶段一主体目标达成，可进入阶段二；存在 1 项阶段一范围内未完成项 + 若干需对齐项，见下文** |

---

## 一、测试结论摘要

| 结论项 | 状态 |
| ------ | ---- |
| 前后端工程骨架可运行 | ✅ 通过 |
| 全部依赖服务（PG/Redis/Qdrant/RabbitMQ/Jaeger）连通 | ✅ 通过 |
| 数据库 12 张表模型落地 + 初始化脚本 | ✅ 通过（存在字段级偏差，见缺陷清单） |
| 底层核心能力（Redis/SSE/异常/配置/Auth/Token/LLM 协议）统一可用 | ✅ 通过 |
| Celery 初始化 + Broker 连通 | ✅ 通过 |
| 前端基础架构（路由/Pinia/Axios/SSE 封装） | ✅ 通过 |
| 前端公共组件（聊天框/上传/报表/Markdown/树/分页表格） | ❌ 未完成（仅 PagePlaceholder） |
| 自动化测试用例（backend/tests） | ⚠️ 目录存在但为空 |

---

## 二、依赖服务连通性测试

| 服务 | 端口 | 测试方式 | 结果 |
| ---- | ---- | -------- | ---- |
| PostgreSQL 15 | 5432 | SQLAlchemy 连接 + `SELECT 1` | ✅ 连通 |
| Redis 7.2 | 6379 | `ping()` + `set_json/get_json` | ✅ 连通 |
| Qdrant | 6333 | `GET /collections` | ✅ 200 |
| RabbitMQ 3.13 | 5672 | Celery `connection().ensure_connection()` | ✅ 连通 |
| Jaeger | 4317/16686 | Docker 容器 Up（otel 未启用，未实际推送） | ✅ 服务就绪 |

> 说明：`backend/.env` 已按 `deploy/docker-compose.yml` 正确配置（PG=bizuser/biz_db、Redis 密码、RabbitMQ admin、Qdrant localhost:6333），`AUTO_INIT_DB=true`。

---

## 三、后端核心能力测试

### 3.1 配置中心 `config/settings.py`

- ✅ `.env` 加载正常，`SQLAlchemy URL` 由 `PG_*` 组件自动拼接（密码经 `quote_plus` 转义）。
- ✅ 派生属性 `cors_origins`、`sqlalchemy_url` 计算正确。
- ✅ 默认值合理（`super_admin_account=admin`、`token_expire_minutes=720`、`max_upload_size_mb=50`）。

### 3.2 系统常量 `config/constants.py`

| 检查项 | 期望 | 实测 | 结果 |
| ------ | ---- | ---- | ---- |
| state 状态位 | 0/1/3 | 0/1/3 | ✅ |
| 分页参数 | 默认10 / 最大100 / 选项[10,20,50,100] | 一致 | ✅ |
| 五级权限 access_type | 1~5 | 1~5 | ✅ |
| 菜单种子 MENU_SEEDS | 6 条 | 6 条 | ✅ |
| Redis Key 模板 | 与设计文档 4.3 一致 | 一致 | ✅ |

### 3.3 `core/` 底层能力

| 模块 | 关键验证 | 结果 |
| ---- | -------- | ---- |
| `redis_client.py` | 连接池 + JSON 读写 + ping | ✅ |
| `exceptions.py` | `AppError` 及 7 个子类 `to_dict()` 输出 `{code,message,data}` | ✅ |
| `sse_generator.py` | `sse_packet`/`text_event`/`done_event`/`status_event`/`error_event` + `stream_to_sse` 异步流转 | ✅ |
| `token_service.py` | `count_tokens`（tiktoken/降级）、`context_usage_ratio`、`needs_compression`、`trim_context` | ✅ |
| `auth.py` | PBKDF2 加盐密码 `hash/verify`（含恒定时间比较）、JWT `create/decode` 往返 | ✅ |
| `permission.py` | `UserContext`、`build_user_context`、`cache/get/clear`、超管判定 | ✅（含 1 项预留 TODO） |
| `llm_client.py` | OpenAI 兼容协议封装、`_extract_content`/`_parse_stream_line` 解析 | ✅（未端到端调用） |
| `database.py` | `Base`/`engine`/`SessionLocal`/`get_db`/`init_db` | ✅ |
| `tracing.py` | OpenTelemetry 初始化（默认关闭，失败降级不阻塞） | ✅ |

### 3.4 异常与接口路由

- ✅ `main.py` 注册全局 `AppError` 与未捕获异常处理器，返回统一结构。
- ✅ 根路由 `/`、`/api/v1/system/*` 挂载成功。

---

## 四、数据库模型与初始化测试

### 4.1 12 张表模型落地

`Base.metadata` 注册表数量 = **12**，与《数据库设计文档 V1.1》表总览一致：

```
sys_department / sys_role / sys_user / sys_user_role / sys_menu /
sys_menu_function / sys_knowledge_category / knowledge_base /
knowledge_permission / chat_session / chat_message / doc_parse_task
```

- ✅ `knowledge_base` 无权限冗余字段（V1.1 合规），仅 `md5` 唯一 + `category_id` 两个索引。
- ✅ `knowledge_permission` 为唯一权限表，`(kb_id,access_type,target_id)` 唯一 + `(access_type,target_id)` 检索主路径索引。
- ✅ `sys_department`/`sys_knowledge_category` 均含 `pid + path` 物化路径。
- ⚠️ 存在若干字段级偏差，见【缺陷清单】。

### 4.2 初始化脚本（建表 + 种子数据）

- ✅ `init_db_and_seed()` 执行成功：建 12 表 + 写菜单 + 建超管 + 清残留缓存。
- ✅ 幂等性：重复执行后 `sys_user=1`、`sys_menu=6`、`sys_department=1`，无重复数据。
- ✅ 种子数据正确：
  - 内置超管 `admin`（dept_id=1、company_id=1、state=0）
  - 根公司节点「企业」（is_company=1、path=`/1/`）
  - 6 条后台菜单（部门/用户/角色/角色授权/知识库分类/知识库上传），state=0

---

## 五、前端基础架构测试

| 检查项 | 结果 |
| ------ | ---- |
| `npm run build` 生产构建 | ✅ 通过（2246 模块，5.41s；仅有 chunk>500kB 警告，非阻断） |
| 路由 `router/index.js` | ✅ 9 条路由 + 登录守卫（未登录跳 `/login`） |
| Pinia `stores/user.js` | ✅ token/userInfo 持久化 + `isLoggedIn`/`isSuper` |
| Axios 封装 `api/request.js` | ✅ 请求注入 Bearer、401 统一登出跳转、错误提示 |
| SSE 封装 `api/sse.js` | ✅ 与后端 `sse_packet` 协议（`event:`/`data:` + 空行）对齐 |
| 公共组件 | ⚠️ 仅 `PagePlaceholder.vue`，其余未实现（见未完成项） |

---

## 六、Celery 初始化测试

- ✅ `tasks/celery_app.py`：broker=RabbitMQ、backend=Redis、路由 `rag`/`report` 队列、`task_acks_late`、`worker_prefetch_multiplier=1`。
- ✅ `celery_worker.py`：Windows 环境 `-P solo` 启动入口，`-Q default,rag,report`。
- ✅ 占位任务 `rag_tasks.health_check` / `parse_document`、`report_tasks.build_report` 已注册。

---

## 七、API 接口冒烟测试（TestClient）

| 接口 | 方法 | 结果 |
| ---- | ---- | ---- |
| `/` | GET | ✅ 200 返回 `{name, version, docs}` |
| `/api/v1/system/info` | GET | ✅ 200 |
| `/api/v1/system/constants` | GET | ✅ 200（分页选项/权限枚举） |
| `/api/v1/system/health` | GET | ✅ 200 `status=ok`，四组件 `application/database/redis/qdrant` 全 True |

> 注意：`auth/chat/rag/report/dept/user/role/menu/category` 等业务路由文件均为空骨架（0 字节），属阶段二~七内容，当前未挂载路由。

---

## 八、缺陷与不一致清单（需开发/设计确认）

| 编号 | 级别 | 位置 | 问题描述 | 建议 |
| ---- | ---- | ---- | -------- | ---- |
| D1 | 中 | `models/sys.py` `SysMenu` | 模型多出设计文档未定义的 `code` 字段；且缺少 `create_time`（设计文档 2.5 含 create_time） | 确认是否保留 `code` 用于后端拦截；补齐 create_time |
| D2 | 中 | `constants.py` 与 `seed.py` | 菜单种子 `MENU_SEEDS` 未设置 `code`，`seed_menus` 以 `m.get("code", m["path"])` 兜底，导致 `sys_menu.code` = 路由路径（如 `/admin/knowledge`）；但 `permission.py` 后端拦截用 `MENU_CODE_*`（如 `knowledge:upload`）。两者不对齐，阶段四授权将失效 | 在 `MENU_SEEDS` 中显式补充 `code` 与 `MENU_CODE_*` 常量映射 |
| D3 | 低 | `models/sys.py` `SysUserRole` | 缺设计文档 2.4 要求的 `create_time` | 视需要补齐 |
| D4 | 低 | `models/sys.py` `SysMenuFunction` | 缺设计文档 2.6 要求的 `create_time` | 视需要补齐 |
| D5 | 低 | `models/knowledge.py` `KnowledgePermission` | 缺设计文档 2.9 要求的 `create_time` | 视需要补齐 |
| D6 | 低 | `models/chat.py` `ChatMessage` | 缺设计文档 2.11 要求的 `create_time`；`token_count` 用 BigInteger（设计为 INT） | 视需要补齐/修正 |
| D7 | 低 | 各模型索引命名 | 与设计文档命名不一致（如 `uk_sys_department_path` vs `uk_path`、`uk_sys_role_name` vs `uk_role_name`），功能等价 | 确认是否统一命名，避免后续歧义 |

> D3~D7 为审计/时间字段与命名类偏差，不影响当前阶段建表与运行，但鉴于开发计划要求「表结构严格按设计文档执行」，建议统一对齐。

---

## 九、未完成项清单（供后续修改维护跟踪）

| 编号 | 类别 | 内容 | 归属阶段 | 说明 |
| ---- | ---- | ---- | -------- | ---- |
| U1 | 阶段一内 | 前端公共组件未实现：聊天框、文档上传、报表图表（当前图表内联于 report 页面）、Markdown 渲染、树组件、分页表格 | 阶段一 | 计划阶段一「公共组件」明确要求，当前仅 `PagePlaceholder.vue` |
| U2 | 阶段一内 | `backend/tests/` 目录为空，无任何单元测试/接口测试 | 阶段一（第九章测试策略） | 建议补充：分页边界、token 统计、异常结构、SSE 报文、权限展开纯函数测试 |
| U3 | 后续 | `core/permission.py` `build_user_context` 仅含当前部门，未做 `path → 祖先部门链` 展开（代码内已标注 TODO 阶段三） | 阶段三 | 预留接口已就绪 |
| U4 | 后续 | `core/llm_client.py` 仅完成协议封装，未做端到端连通验证（本地 LLM 服务未启动） | 阶段五 | 依赖 `LLM_BASE_URL=http://localhost:8000/v1` |
| U5 | 后续 | `tasks/rag_tasks.py`、`tasks/report_tasks.py` 均为占位任务，无实际解析/报表逻辑 | 阶段六/七 | 骨架已就绪 |
| U6 | 后续 | `api/v1` 下 auth/chat/rag/report/dept/user/role/menu/category 及对应 service/repo/schema 均为空骨架（0 字节） | 阶段二~七 | 符合分阶段规划，非缺陷 |
| U7 | 后续 | 前端登录页为「演示模式」占位，真实登录鉴权未接通 | 阶段二 | 已预留 `api/auth.js` 封装 |

---

## 十、需要人工确认的事项（含具体步骤）

### 10.1 浏览器 UI 验证（前端页面展示）

阶段一涉及页面渲染，建议人工确认：

1. `cd frontend` 后执行 `npm run dev`，浏览器打开 `http://localhost:5173`。
2. 确认顶部「商枢 BizPivot」品牌栏与右侧健康标签显示 **「服务正常」**（后端需已启动）。
3. 访问 `/login`，点击 **「跳过登录，进入系统」** 进入演示模式，确认跳转 `/chat`。
4. 依次访问 `/chat`、`/report`、`/admin/dept`~`/admin/knowledge`，确认各占位页正常渲染、报表页 ECharts 图表显示。

### 10.2 Celery Worker 端到端验证

1. `cd backend`，执行 `celery -A app.tasks.celery_app:celery_app worker -l info -P solo -Q default,rag,report`（或 `python celery_worker.py`）。
2. 在另一个终端执行 `python -c "from app.tasks.rag_tasks import health_check; print(health_check.delay().get(timeout=10))"`。
3. 期望返回 `{"status":"ok", ...}`，确认 worker 收到任务并执行。

### 10.3 LLM 服务端到端验证（阶段五前可跳过）

1. 本地启动任一 OpenAI 兼容推理服务并监听 `8000` 端口（如 vLLM/Ollama），模型名与 `.env` 的 `LLM_MODEL=qwen-plus` 对齐。
2. 执行冒烟：`python -c "import asyncio; from app.core.llm_client import get_llm_client; print(asyncio.run(get_llm_client().generate([{'role':'user','content':'你好'}])))"`。
3. 期望返回模型文本回复。

### 10.4 OpenTelemetry / Jaeger 链路追踪验证

1. 将 `backend/.env` 中 `OTEL_ENABLED` 改为 `true`，重启后端。
2. 访问若干接口后，浏览器打开 `http://localhost:16686`（Jaeger UI）。
3. 在 Service 下拉中选择 `biz-pivot-fastapi`，确认能看到链路 Span。

### 10.5 缺陷 D1/D2 的取舍确认

需开发/设计确认：`sys_menu.code` 字段是否保留；菜单权限标识统一采用「路由路径」还是 `MENU_CODE_*` 常量（`dept:manage`/`knowledge:upload` 等），以便阶段四授权逻辑对齐。

---

## 十一、附录：本次测试关键执行命令

```powershell
# 依赖连通 + 模型 + 纯函数 + 接口冒烟（工作目录 backend，使用 .venv）
& "..\.venv\Scripts\python.exe" -c "from app.models.seed import init_db_and_seed; init_db_and_seed()"
& "..\.venv\Scripts\python.exe" -c "import app.models; from app.core.database import Base; print(len(Base.metadata.tables))"

# 健康检查接口（TestClient）
& "..\.venv\Scripts\python.exe" -c "from fastapi.testclient import TestClient; from app.main import app; print(TestClient(app).get('/api/v1/system/health').json())"

# 前端生产构建
npm run build
```

> 注：本报告仅覆盖阶段一，未修改任何源代码；数据库初始化/种子数据为幂等操作，与系统启动时 `AUTO_INIT_DB=true` 行为一致。
