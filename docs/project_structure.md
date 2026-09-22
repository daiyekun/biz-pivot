# Project Structure 项目目录结构文档

## 1\. 项目基础信息

- **项目名称**：BizPivot（商枢）

- **项目定位**：企业家AI助手（RAG私有知识库 \+ AI闲聊对话 \+ 智能数据报表）

- **技术架构**：Vue3 \+ Vite 前端 \+ FastAPI Python 后端

- **架构模式**：前后端分离、单体起步、可平滑微服务/分布式扩容

- **核心能力**：流式AI对话、上下文智能管理、RAG文档问答、异步文档解析、智能数据报表

## 2\. 全局命名规范（强制统一）

### 2\.1 目录/文件命名

- 根目录、前端静态目录、部署目录：**小写短横线 kebab\-case**

- Python 包、模块、脚本：**小写下划线 snake\_case**

- Markdown 文档：小写下划线，禁止中文、空格、大写乱码

- 配置常量、枚举：全大写下划线

### 2\.2 代码分层调用规则（单向依赖，禁止反向）

API路由层 → Service业务层 → Repository仓储层 → 核心工具/存储

异步任务层\(Tasks\) → Service业务层 → Repository仓储层

**禁止规则**：

- 路由层不写任何业务逻辑、数据处理逻辑

- 业务层不直接操作数据库、Redis、向量库，必须走仓储层

- 所有耗时IO（文档解析、报表计算）必须放入Celery异步任务

- 所有会话、上下文状态外置Redis，禁止内存存储（适配分布式部署）

## 3\. 完整项目目录树

```Plain Text
biz-pivot/
├── frontend/                     # Vue3 前端项目
│   ├── public/                   # 静态资源
│   ├── src/
│   │   ├── api/                 # Axios普通接口 + SSE流式接口封装
│   │   ├── components/          # 公共组件：聊天框、文档上传、报表图表、Markdown渲染
│   │   ├── views/               # 页面视图：对话页、RAG文档管理页、报表工作台、系统设置页
│   │   ├── stores/              # Pinia全局状态：对话列表、模型配置、全局参数
│   │   ├── utils/               # 前端通用工具方法
│   │   ├── App.vue
│   │   └── main.js
│   ├── vite.config.js
│   └── package.json
│
├── backend/                      # FastAPI Python 后端核心
│   ├── app/
│   │   ├── main.py               # 项目入口：注册路由、全局异常、CORS、生命周期
│   │   ├── config/               # 全局配置中心
│   │   │   ├── settings.py       # 环境变量、全局参数、第三方服务配置
│   │   │   └── constants.py      # 系统常量：上下文阈值、最大Token、分页参数
│   │   │
│   │   ├── api/                  # 路由控制层（仅参数校验、请求转发）
│   │   │   ├── deps.py           # 全局依赖：会话校验、权限拦截
│   │   │   └── v1/               # V1版本接口管理
│   │   │       ├── chat.py       # AI对话SSE流式接口
│   │   │       ├── rag.py        # 文档上传、解析、检索、管理接口
│   │   │       ├── report.py     # 智能数据报表查询、生成接口
│   │   │       └── system.py     # 系统配置、健康检查、模型配置接口
│   │   │
│   │   ├── core/                 # 底层核心能力（全局复用、无业务耦合）
│   │   │   ├── token_service.py  # Token统计、上下文占用率、自动压缩/摘要
│   │   │   ├── llm_client.py     # 统一LLM客户端（兼容OpenAI/Ollama/国产模型）
│   │   │   ├── sse_generator.py  # SSE流式消息统一封装（状态推送+文本流推送）
│   │   │   ├── redis_client.py   # Redis全局连接、缓存工具
│   │   │   └── exceptions.py     # 全局异常定义与统一捕获处理
│   │   │
│   │   ├── services/             # 核心业务服务层（所有业务逻辑实现）
│   │   │   ├── chat_service.py   # 对话管理、上下文加载、压缩、历史管理
│   │   │   ├── rag_service.py    # 文档解析、切片、向量化、向量检索编排
│   │   │   ├── report_service.py # 数据统计、报表计算、图表数据生成
│   │   │   └── file_service.py   # 文件读写、对象存储（MinIO）管理
│   │   │
│   │   ├── tasks/                # Celery异步重型任务（解耦耗时操作）
│   │   │   ├── celery_app.py     # Celery实例初始化、队列配置
│   │   │   ├── rag_tasks.py      # 文档异步解析、切片、向量入库任务
│   │   │   └── report_tasks.py   # 后台报表批量计算、数据汇总任务
│   │   │
│   │   ├── repositories/         # 数据仓储层（隔离所有存储介质）
│   │   │   ├── chat_repo.py      # 对话会话、上下文Redis读写
│   │   │   ├── doc_repo.py       # 文档元数据数据库读写
│   │   │   └── vector_repo.py    # 向量库（Qdrant/Chroma/Milvus）读写封装
│   │   │
│   │   ├── schemas/              # Pydantic数据模型（入参、出参、数据结构体）
│   │   │   ├── chat_schema.py
│   │   │   ├── rag_schema.py
│   │   │   └── report_schema.py
│   │   │
│   │   └── utils/                # 通用工具函数
│   │       ├── text_utils.py
│   │       └── time_utils.py
│   │
│   ├── tests/                    # 单元测试、接口测试用例
│   ├── .env.example              # 环境变量模板（提交Git）
│   ├── requirements.txt          # Python依赖清单
│   ├── Dockerfile                # 后端容器构建文件
│   └── celery_worker.py          # Celery Worker启动入口
│
├── docs/                         # 项目全套文档
│   ├── README.md                 # 文档首页
│   ├── project_structure.md      # 【本文档】项目目录与架构说明
│   ├── architecture.md           # 系统分布式架构、微服务演进方案
│   ├── api_spec.md               # 统一接口文档
│   ├── environment.md            # 环境部署、依赖安装指南
│   └── knowledge/                # RAG私有知识库素材（*.md业务文档）
│
├── deploy/                       # 项目部署资源
│   ├── nginx/                    # Nginx反向代理、负载均衡配置
│   └── docker-compose.yml        # 本地全套服务一键启动（Redis+向量库+后端）
│
├── .gitignore
└── README.md                     # 项目总说明、快速启动手册
```

## 4\. 核心目录详细职责说明

### 4\.1 前端 frontend

- **api**：封装所有后端请求，包含普通POST/GET接口、SSE长链接流式接口

- **components**：复用UI组件，纯展示无复杂逻辑，解耦页面

- **views**：页面入口，组装组件、处理页面交互逻辑

- **stores**：全局状态管理，存储对话历史、系统配置，适配页面刷新持久化

### 4\.2 后端核心分层（最重要）

#### 4\.2\.1 config 配置层

统一管理所有环境变量、第三方服务地址、系统阈值，全局唯一配置入口，方便环境切换、线上线下隔离。

#### 4\.2\.2 api 路由层

只做三件事：接收参数、参数校验、调用Service、返回结果。**不写任何业务逻辑**，保证接口轻量化。

#### 4\.2\.3 core 核心层

项目底层底座，无业务耦合，可全局复用：Token计算、LLM请求、SSE推送、Redis连接、异常统一处理。是支撑AI能力的基础。

#### 4\.2\.4 services 业务层

项目核心业务逻辑全部在此：对话上下文管理、RAG检索编排、报表数据计算、文件处理。是整个项目的业务中枢。

#### 4\.2\.5 tasks 异步任务层

专门承载**耗时、阻塞型任务**：大文件解析、批量向量化、复杂报表计算。避免阻塞Web服务，大幅提升并发和用户体验。

#### 4\.2\.6 repositories 仓储层

隔离所有存储介质（Redis、MySQL、向量库、文件存储），业务层无需感知存储细节，方便后期切换数据库、分布式扩容。

#### 4\.2\.7 schemas 模型层

统一请求、响应、数据库数据结构，自动参数校验、类型约束，保证接口规范统一。

## 5\. 文档目录规范

- **docs/project\_structure\.md**：当前文件，团队开发统一目录标准

- **docs/knowledge/**：存放所有RAG私有知识库文档，统一命名 `xxx_xxx.md`

- **\.env\.example**：公开环境变量模板，不含密钥，供团队同步配置

- **\.env**：本地私有配置，禁止提交Git

## 6\. 分布式/微服务扩容预留设计

当前为单体架构，目录结构**完全支持后期无痛拆分微服务**：

1. **chat\-service**：拆分 chat 相关 api、service、repo，独立部署（SSE对话服务）

2. **rag\-service**：拆分 RAG 文档解析、向量检索、异步任务，独立部署

3. **report\-service**：拆分报表计算、数据统计服务，独立部署

所有公共能力（core/config/utils）可抽离为公共SDK包，多服务共享。

## 7\. 核心工程优势

- 分层清晰、职责单一，新人可快速上手开发

- 适配AI场景：SSE流式、上下文管理、异步RAG任务

- 原生支持分布式部署：无内存状态、Redis外置会话

- 可平滑演进：单体 → 微服务 → K8s容器化

- 前后端完全解耦，可网页运行、可无缝迁移桌面端

> 