# 商枢 BizPivot 数据库详细设计文档 V1.2（PostgreSQL 版）

## 1. 文档说明与约定

### 1.1 文档目的

本文档在 `dbinfo.md` 基础设计之上，补齐完整表结构、字段、索引、权限模型与高并发检索方案，作为后端开发、RAG 检索过滤、异步任务落地的唯一数据库依据。**本文档以 PostgreSQL 15+ 为标准。**

**V1.1 变更说明：**



* 移除文档中复杂的检索权限过滤 SQL（多分支 OR 查询），当前开发阶段不落地

* 权限设计改为「统一明细表」：五级权限全部展开写入 `knowledge_permission`，`knowledge_base` 不再冗余权限字段

* `knowledge_base` 索引从 7 个精简为 2 个，降低插入写放大

* 检索权限过滤以 Redis 白名单 + Qdrant payload 过滤为主路径

**V1.2 变更说明：**



* 新增 `sys_provider`（模型提供商）与 `sys_chat_role`（智能聊天角色）两张表

* `chat_session` 新增 `chat_role_id` 外键，强制会话关联聊天角色（先选角色才能建会话）

* `chat_message.role` 由 0=用户/1=AI 扩展为枚举：0=系统 1=用户 2=助手 3=工具

### 1.2 设计原则



| 原则    | 说明                                             |
| ----- | ---------------------------------------------- |
| 查询优先  | 检索以「权限白名单 + 向量库过滤」为主，避免复杂 SQL                  |
| 权限归一  | 五级权限统一收敛到 `knowledge_permission` 明细表，单一事实来源    |
| 低写放大  | 高频表（knowledge\_base）只保留必要索引，上传低频写入不拖累          |
| 保留原设计 | `sys_department.is_company`（公司即部门节点）、表名风格沿用原文档 |

### 1.3 通用约定



* 数据库：**PostgreSQL 15+**，字符集 UTF8

* 主键：`id BIGINT GENERATED ALWAYS AS IDENTITY`（PG 标准自增写法）

* 所有表包含 `create_time`、`update_time`（`TIMESTAMP`，默认 `now()`）

* `update_time` 维护方式：**应用层统一更新**（推荐，简单可控）；或建触发器 `BEFORE UPDATE ... SET update_time = now()`（可选）

* 状态字段 `state`：0 = 启用 / 显示，1 = 禁用 / 不显示，3 = 删除（软删除），类型 `SMALLINT`

* 布尔 / 小枚举统一用 `SMALLINT`（0/1），不依赖 PG boolean，避免 ORM 映射差异

* 表名前缀：`sys_` 系统管理、`knowledge_` 知识库、`chat_` 对话、`doc_` 文档任务

* 索引命名：`uk_` 唯一索引、`idx_` 普通索引

### 1.4 表总览



| 序号 | 表名                       | 用途          | 来源                  |
| -- | ------------------------ | ----------- | ------------------- |
| 1  | sys\_department          | 部门 / 公司（树形） | 原文档完善               |
| 2  | sys\_role                | 角色          | 原文档完善               |
| 3  | sys\_user                | 用户          | 原文档完善               |
| 4  | sys\_user\_role          | 用户 - 角色关联   | **新增**              |
| 5  | sys\_menu                | 菜单定义        | **新增**              |
| 6  | sys\_menu\_function      | 角色 - 菜单权限   | 原文档补全               |
| 7  | sys\_knowledge\_category | 知识分类（树形）    | 原文档完善               |
| 8  | knowledge\_base          | 知识库文档主表     | 原文档完善（V1.1 去权限冗余字段） |
| 9  | knowledge\_permission    | 知识库权限明细表    | **新增（V1.1 唯一权限表）**  |
| 10 | chat\_session            | 对话会话        | **新增（V1.2 关联聊天角色）**              |
| 11 | chat\_message            | 对话消息        | **新增（V1.2 角色枚举）**              |
| 12 | doc\_parse_task         | 文档异步解析任务    | **新增**              |
| 13 | sys\_provider           | 模型提供商        | **新增（V1.2）**              |
| 14 | sys\_chat\_role         | 智能聊天角色      | **新增（V1.2）**              |
| 15 | sys\_role\_category     | 角色 - 可访问知识分类 | **新增（V1.3 阶段四）**              |



***

## 2. 表结构详细设计

### 2.1 sys\_department（部门 / 公司表，树形）

> 设计要点：
>
> `is_company`
>
>  区分公司节点与部门节点，公司是部门树的根级节点；
> `path`
>
> **&#x20;物化路径字段**
>
> （如 
>
> `/1/3/5/`
>
> ），用于快速计算用户部门链与「部门及子部门」展开，避免递归遍历。



| 字段           | 描述        | 类型           | 默认       | 备注                        |
| ------------ | --------- | ------------ | -------- | ------------------------- |
| id           | 部门 / 公司主键 | BIGINT       | IDENTITY | 主键自增                      |
| pid          | 上级节点 ID   | BIGINT       | 0        | 值来源本表 id；0 = 顶级（公司）       |
| name         | 名称        | VARCHAR(200) | -        | 公司名或部门名                   |
| is\_company  | 是否公司节点    | SMALLINT     | 0        | 0 = 部门，1 = 公司             |
| company\_id  | 所属公司 ID   | BIGINT       | 0        | 冗余：公司节点自身 id，部门节点填所属公司 id |
| path         | 物化路径      | VARCHAR(500) | '/'      | 如 `/1/3/5/`，含自身           |
| sort\_order  | 排序        | INT          | 0        | 同级排序                      |
| state        | 状态        | SMALLINT     | 0        | 0 = 显示 1 = 不显示 3 = 删除     |
| create\_time | 创建时间      | TIMESTAMP    | now()    |                           |
| update\_time | 更新时间      | TIMESTAMP    | now()    | 应用层维护                     |

**索引：**



| 索引名          | 字段          | 类型 | 说明     |
| ------------ | ----------- | -- | ------ |
| uk\_path     | path        | 唯一 | 防止路径冲突 |
| idx\_pid     | pid         | 普通 | 查子节点   |
| idx\_company | company\_id | 普通 | 按公司查部门 |

### 2.2 sys\_role（角色表）



| 字段           | 描述   | 类型           | 默认       | 备注            |
| ------------ | ---- | ------------ | -------- | ------------- |
| id           | 角色主键 | BIGINT       | IDENTITY | 主键自增          |
| name         | 角色名称 | VARCHAR(50)  | -        |               |
| desc         | 角色描述 | VARCHAR(500) | -        |               |
| state        | 状态   | SMALLINT     | 0        | 0 = 启用 1 = 禁用 |
| create\_time | 创建时间 | TIMESTAMP    | now()    |               |
| update\_time | 更新时间 | TIMESTAMP    | now()    | 应用层维护         |

**索引：** `uk_role_name`（name 唯一）

### 2.3 sys\_user（用户表）

> 原文档已含 account/pwd/slot/dept_id，补充角色关联（多对多，见 2.4）与常用业务字段。



| 字段           | 描述          | 类型           | 默认       | 备注                    |
| ------------ | ----------- | ------------ | -------- | --------------------- |
| id           | 用户主键        | BIGINT       | IDENTITY | 主键自增                  |
| name         | 显示名称        | VARCHAR(50)  | -        |                       |
| account      | 登录账号        | VARCHAR(50)  | -        | 唯一索引                  |
| pwd          | 密码          | VARCHAR(100) | -        | 加密存储                  |
| slot         | 加盐串         | VARCHAR(100) | -        | 配合密码加解密               |
| dept\_id     | 部门 ID       | BIGINT       | -        | 外键→sys\_department，必填 |
| company\_id  | 所属公司 ID（冗余） | BIGINT       | 0        | 冗余，权限主体集合计算用          |
| phone        | 手机号         | VARCHAR(20)  | -        | 可选                    |
| email        | 邮箱          | VARCHAR(100) | -        | 可选                    |
| state        | 状态          | SMALLINT     | 0        | 0 = 启用 1 = 禁用         |
| create\_time | 创建时间        | TIMESTAMP    | now()    |                       |
| update\_time | 更新时间        | TIMESTAMP    | now()    | 应用层维护                 |

**索引：**



| 索引名          | 字段          | 说明     |
| ------------ | ----------- | ------ |
| uk\_account  | account     | 登录唯一   |
| idx\_dept    | dept\_id    | 按部门查用户 |
| idx\_company | company\_id | 按公司查用户 |

### 2.4 sys\_user\_role（用户 - 角色关联表）【新增】

> 用户与角色多对多：一个用户可有多个角色，一个角色可有多个用户。
> 角色授权即时生效：登录时一次性加载用户角色集合进 Redis。



| 字段           | 描述    | 类型        | 备注           |
| ------------ | ----- | --------- | ------------ |
| id           | 主键    | BIGINT    | IDENTITY     |
| user\_id     | 用户 ID | BIGINT    | 外键→sys\_user |
| role\_id     | 角色 ID | BIGINT    | 外键→sys\_role |
| create\_time | 创建时间  | TIMESTAMP | now()        |

**索引：** `uk_user_role`（user\_id, role\_id 唯一）；`idx_role`（role\_id）

### 2.5 sys\_menu（菜单定义表）【新增】

> 原文档只有角色 - 菜单关联表，缺少菜单本身定义。菜单初始化数据在系统启动时写入（部门管理、用户管理、角色管理、角色授权、知识库分类、知识库上传、模型提供商、聊天角色）。



| 字段           | 描述     | 类型           | 默认       | 备注            |
| ------------ | ------ | ------------ | -------- | ------------- |
| id           | 菜单 ID  | BIGINT       | IDENTITY | 主键自增          |
| parent\_id   | 父菜单 ID | BIGINT       | 0        | 0 = 顶级（用于菜单树） |
| name         | 菜单名称   | VARCHAR(50)  | -        |               |
| path         | 前端路由   | VARCHAR(100) | -        | 如 /admin/user |
| code         | 权限标识   | VARCHAR(50)  | ''       | 如 `dept:manage`、`knowledge:upload`（阶段四后端拦截核心标识） |
| icon         | 图标     | VARCHAR(50)  | -        |               |
| sort\_order  | 排序     | INT          | 0        |               |
| page\_type   | 页面类型   | VARCHAR(20)  | -        | `tree`=树形（不分页） `list`=分页列表 |
| state        | 状态     | SMALLINT     | 0        | 0 = 启用 1 = 禁用 |
| create\_time | 创建时间   | TIMESTAMP    | now()    |               |

**索引：** `idx_parent`（parent\_id）

### 2.6 sys\_menu\_function（角色 - 菜单权限表）【补全】

> 原文档只有 menu_id，补上 role_id 形成完整 RBAC 关联：角色 → 可访问菜单集合。



| 字段           | 描述    | 类型        | 备注           |
| ------------ | ----- | --------- | ------------ |
| id           | 主键    | BIGINT    | IDENTITY     |
| role\_id     | 角色 ID | BIGINT    | 外键→sys\_role |
| menu\_id     | 菜单 ID | BIGINT    | 外键→sys\_menu |
| create\_time | 创建时间  | TIMESTAMP | now()        |

**索引：** `uk_role_menu`（role\_id, menu\_id 唯一）；`idx_menu`（menu\_id）

### 2.6a sys\_role\_category（角色 - 可访问知识分类表）【V1.3 阶段四新增】

> 角色授权「知识库权限配置」中的「可访问知识库分类范围」落地于此表。空集合 = 不限制（可访问全部分类）；检索时与 `knowledge_permission` 明细表叠加过滤（阶段六生效）。



| 字段           | 描述     | 类型        | 备注                     |
| ------------ | ------ | --------- | ---------------------- |
| id           | 主键     | BIGINT    | IDENTITY               |
| role\_id     | 角色 ID  | BIGINT    | 外键→sys\_role           |
| category\_id | 分类 ID  | BIGINT    | 外键→sys\_knowledge\_category |
| create\_time | 创建时间   | TIMESTAMP | now()                  |

**索引：** `uk_role_category`（role\_id, category\_id 唯一）；`idx_category`（category\_id）

### 2.7 sys\_knowledge\_category（知识分类表，树形）

> 原文档含 id/name/pid，补排序、状态、时间字段。无限级树，检索文档按分类过滤走 category_id 索引。



| 字段           | 描述      | 类型           | 默认       | 备注                    |
| ------------ | ------- | ------------ | -------- | --------------------- |
| id           | 分类主键    | BIGINT       | IDENTITY | 主键自增                  |
| name         | 类别名称    | VARCHAR(50)  | -        |                       |
| pid          | 上级分类 ID | BIGINT       | 0        | 值来源本表 id              |
| path         | 物化路径    | VARCHAR(500) | '/'      | 如 `/1/2/`，含自身         |
| sort\_order  | 排序      | INT          | 0        |                       |
| state        | 状态      | SMALLINT     | 0        | 0 = 显示 1 = 不显示 3 = 删除 |
| create\_time | 创建时间    | TIMESTAMP    | now()    |                       |
| update\_time | 更新时间    | TIMESTAMP    | now()    | 应用层维护                 |

**索引：** `idx_pid`（pid）；`idx_path`（path）

### 2.8 knowledge\_base（知识库文档主表）【V1.1 精简】

> V1.1：
>
> **移除权限冗余字段**
>
> （permission_type /owner_user_id/dept_id /company_id），权限统一放 
>
> `knowledge_permission`
>
> ；
> 索引精简为 2 个，插入写放大最小化。



| 字段               | 描述       | 类型            | 默认       | 备注                            |
| ---------------- | -------- | ------------- | -------- | ----------------------------- |
| id               | 文档主键     | BIGINT        | IDENTITY | 主键自增                          |
| file\_name       | 知识库文件名称  | VARCHAR(500)  | -        |                               |
| md5              | 文件摘要     | VARCHAR(200)  | -        | 唯一索引，防重复上传                    |
| file\_path       | 文件路径     | VARCHAR(800)  | -        | 存储 MinIO / 本地                 |
| file\_size       | 文件大小（字节） | BIGINT        | 0        |                               |
| category\_id     | 归属分类     | BIGINT        | -        | 外键→sys\_knowledge\_category   |
| description      | 知识库描述    | VARCHAR(1000) | -        | 上传必填                          |
| create\_user\_id | 创建人      | BIGINT        | -        | 外键→sys\_user                  |
| parse\_status    | 解析状态     | SMALLINT      | 0        | 0 = 待解析 1 = 解析中 2 = 成功 3 = 失败 |
| vector\_status   | 向量化状态    | SMALLINT      | 0        | 0 = 未入库 1 = 已入库 2 = 失败        |
| chunk\_count     | 切片数量     | INT           | 0        |                               |
| state            | 状态       | SMALLINT      | 0        | 0 = 显示 1 = 不显示 3 = 删除         |
| create\_time     | 创建时间     | TIMESTAMP     | now()    |                               |
| update\_time     | 更新时间     | TIMESTAMP     | now()    | 应用层维护                         |

**索引（仅保留必要，低写放大）：**



| 索引名           | 字段           | 说明           |
| ------------- | ------------ | ------------ |
| uk\_md5       | md5          | 防重复上传        |
| idx\_category | category\_id | 分类过滤（上传必选分类） |

### 2.9 knowledge\_permission（知识库权限明细表）【V1.1 唯一权限表・核心】

> **设计**
>
> ：五级权限
>
> **全部展开**
>
> 为明细行，本表是权限判定的
>
> **唯一数据来源**
>
> 。
> 每行 = 文档 + 一个可访问主体（用户 / 部门 / 公司），配合索引毫秒级过滤，检索 SQL 极简。



| 字段           | 描述    | 类型        | 备注                                      |
| ------------ | ----- | --------- | --------------------------------------- |
| id           | 主键    | BIGINT    | IDENTITY                                |
| kb\_id       | 文档 ID | BIGINT    | 外键→knowledge\_base.id                   |
| access\_type | 主体类型  | SMALLINT  | 1 = 用户 2 = 部门 3 = 公司 4 = 部门及子部门 5 = 跨部门 |
| target\_id   | 主体 ID | BIGINT    | 用户 ID 或 部门 ID 或 公司 ID                   |
| create\_time | 创建时间  | TIMESTAMP | now()                                   |

**索引：**



| 索引名            | 字段                                 | 说明                    |
| -------------- | ---------------------------------- | --------------------- |
| uk\_kb\_target | (kb\_id, access\_type, target\_id) | 唯一，防重复授权              |
| idx\_target    | (access\_type, target\_id)         | **检索主路径**：给定主体反查可访问文档 |

**数据写入约定（上传时统一展开）：**



| 权限类型     | 展开方式                                                     |
| -------- | -------------------------------------------------------- |
| 1 个人     | 写 1 行：access\_type=1, target\_id = 上传者用户 ID              |
| 2 部门     | 写 1 行：access\_type=2, target\_id = 所选部门 ID               |
| 3 公司     | 写 1 行：access\_type=3, target\_id = 所选公司 ID               |
| 4 部门及子部门 | 写 N 行：access\_type=4，目标部门 + 全部子孙部门各一行（用 path 展开，避免检索时递归） |
| 5 跨部门    | 写 N 行：access\_type=5，每个被选部门一行                            |



* 部门结构变更（新增 / 移动 / 删除部门）→ 触发异步任务重建受影响文档的 access\_type=4 展开行

* 删除文档 → 同步删除该 kb\_id 全部权限行

### 2.10 chat\_session（对话会话表）【V1.2 关联聊天角色】



| 字段           | 描述   | 类型           | 备注            |
| ------------ | ---- | ------------ | ------------- |
| id           | 会话主键 | BIGINT       | IDENTITY      |
| user\_id     | 所属用户 | BIGINT       | 外键→sys\_user  |
| chat\_role\_id | 聊天角色ID | BIGINT     | 外键→sys\_chat\_role，**必填（先选角色才能建会话）** |
| title        | 会话标题 | VARCHAR(200) |               |
| state        | 状态   | SMALLINT     | 0 = 正常 3 = 删除 |
| create\_time | 创建时间 | TIMESTAMP    | now()         |
| update\_time | 更新时间 | TIMESTAMP    | now()         |

**索引：** `idx_user_time`（user\_id, update\_time）—— 会话列表按时间倒序；`idx_session_role`（chat\_role\_id）—— 按角色反查会话

### 2.11 chat\_message（对话消息表）【V1.2 角色枚举】



| 字段           | 描述      | 类型        | 备注               |
| ------------ | ------- | --------- | ---------------- |
| id           | 消息主键    | BIGINT    | IDENTITY         |
| session\_id  | 会话 ID   | BIGINT    | 外键→chat\_session |
| role         | 消息角色    | SMALLINT  | **枚举：0=系统 1=用户 2=助手 3=工具** |
| content      | 消息内容    | TEXT      |                  |
| token\_count | token 数 | INT       | 用于统计             |
| create\_time | 创建时间    | TIMESTAMP | now()            |

**索引：** `idx_session_time`（session\_id, id）—— 按会话拉取消息

### 2.12 doc\_parse\_task（文档解析任务表）【新增】

> 知识库上传后 Celery 异步解析、切片、向量化入库，任务状态落表，支持进度展示与失败重试。



| 字段               | 描述           | 类型            | 备注                            |
| ---------------- | ------------ | ------------- | ----------------------------- |
| id               | 任务主键         | BIGINT        | IDENTITY                      |
| kb\_id           | 文档 ID        | BIGINT        | 外键→knowledge\_base            |
| task\_type       | 任务类型         | SMALLINT      | 1 = 解析切片 2 = 向量化              |
| status           | 状态           | SMALLINT      | 0 = 待执行 1 = 执行中 2 = 成功 3 = 失败 |
| retry\_count     | 重试次数         | INT           | 0                             |
| error\_msg       | 错误信息         | VARCHAR(1000) |                               |
| celery\_task\_id | Celery 任务 ID | VARCHAR(100)  | 关联链路追踪                        |
| create\_time     | 创建时间         | TIMESTAMP     | now()                         |
| update\_time     | 更新时间         | TIMESTAMP     | now()                         |

**索引：** `idx_kb`（kb\_id）；`idx_status`（status）

### 2.13 sys\_provider（模型提供商表）【V1.2 新增】

> 后台【模型提供商】页面配置多个提供商，聊天角色通过 `provider_id` 绑定指定提供商；未绑定时回退到 .env 默认 LLM 配置。



| 字段           | 描述     | 类型           | 默认   | 备注              |
| ------------ | ------ | ------------ | ---- | --------------- |
| id           | 提供商主键  | BIGINT       | IDENTITY | 主键自增            |
| name         | 提供商名称  | VARCHAR(100) | -    | 唯一索引            |
| endpoint     | API调用地址 | VARCHAR(255) | -    | 如 https://x/v1  |
| model        | 模型名称   | VARCHAR(100) | -    |                 |
| api\_key     | API密钥  | VARCHAR(500) | ''   | 敏感信息，列表脱敏       |
| create\_time | 创建时间   | TIMESTAMP    | now() |                 |
| update\_time | 更新时间   | TIMESTAMP    | now() | 应用层维护           |

**索引：** `uk_provider_name`（name 唯一）

### 2.14 sys\_chat\_role（智能聊天角色表）【V1.2 新增】

> 聊天角色绑定系统提示词、模型温度与模型提供商；系统发起聊天（意图识别/语义识别等）由程序直接指定内置角色。



| 字段             | 描述      | 类型           | 默认  | 备注                        |
| -------------- | ------- | ------------ | --- | ------------------------- |
| id             | 角色主键    | BIGINT       | IDENTITY | 主键自增                      |
| name           | 角色名称    | VARCHAR(100) | -   | 唯一索引                      |
| description    | 角色描述    | VARCHAR(200) | -   | 可空                        |
| system\_prompt | 系统提示词   | VARCHAR(4000) | -   | 可空                        |
| temperature    | 模型温度    | FLOAT        | 0.7 | 默认 0.7                    |
| provider\_id   | 模型提供商ID | BIGINT       | -   | 外键→sys\_provider，可空        |
| create\_time   | 创建时间    | TIMESTAMP    | now() |                           |
| update\_time   | 更新时间    | TIMESTAMP    | now() | 应用层维护                     |

**索引：** `uk_chat_role_name`（name 唯一）；`idx_chat_role_provider`（provider\_id）



***

## 3. 知识库权限设计（检索过滤方案）

### 3.1 五级权限模型（统一明细表）



| 权限类型     | 表设计                           | 可访问主体          |
| -------- | ----------------------------- | -------------- |
| 1 个人     | knowledge\_permission 1 行     | 仅上传者本人         |
| 2 部门     | knowledge\_permission 1 行     | 该部门直属员工        |
| 3 公司     | knowledge\_permission 1 行     | 该公司所有部门员工      |
| 4 部门及子部门 | knowledge\_permission N 行（展开） | 该部门 + 所有子孙部门员工 |
| 5 跨部门    | knowledge\_permission N 行     | 被选中的多个部门员工     |

### 3.2 用户可访问主体集合（一次计算，处处复用）

用户登录 / 检索时，计算 "主体集合" 并缓存到 Redis（key: `user:perm:{uid}`）：



```
my\_user\_id        = 当前用户ID

my\_company\_id     = sys\_user.company\_id（冗余）

my\_dept\_ids       = 当前部门 + 所有祖先部门ID（由 sys\_department.path 解析，如 /1/3/5/ → \[5,3,1]）
```

### 3.3 检索权限过滤方案（V1.1：不落地复杂 SQL）

**当前开发阶段，权限过滤不通过复杂数据库 SQL 实现，按以下主路径：**



```
用户提问

&#x20; → ① Redis 白名单命中：user:docs:{uid} → 直接拿可访问 doc\_id 集合

&#x20; → ② 未命中：knowledge\_permission 单表简单查询回填（见下方兜底 SQL）

&#x20; → ③ Qdrant 检索，filter: doc\_id IN (白名单) AND category\_id = ?

&#x20; → 返回有权片段 → LLM 生成
```

**DB 侧兜底（缓存未命中时执行，单表简单查询）：**



```
SELECT DISTINCT kp.kb\_id

FROM knowledge\_permission kp

WHERE kp.target\_id IN (:my\_user\_id, :my\_dept\_ids, :my\_company\_id);
```

> 单一条件 + IN 查询，全部走 
>
> `idx_target`
>
>  索引，无多分支 OR、无子查询。
> 权限变更（上传 / 删除 / 授权调整）时主动删除对应 Redis 缓存，保证实时生效。

### 3.4 部门及子部门展开策略



* **写入时展开**（推荐）：授权部门 X 时，用 `path LIKE '/X/%'` 或递归 CTE 查全部子孙，每个子孙写一行

* **读取时兜底**：用户部门链天然包含祖先部门，单表 IN 查询天然兼容

* 部门结构变更（新增 / 移动 / 删除）→ 异步任务重建受影响文档展开行



***

## 4. 高并发性能设计（PostgreSQL 专项）

### 4.1 索引策略汇总（防全表扫描）



* 所有外键列、过滤条件列建立索引（已在各表标注）

* 权限检索只依赖 `knowledge_permission.idx_target` 一个主路径索引

* `knowledge_base` 保持最少索引（2 个），上传插入写放大最小

* PG 特性补充：若未来「跨部门」改用数组存储（`BIGINT[]`），可用 **GIN 索引** + `@>` 操作符；当前明细表方案普通 B-tree 即可

### 4.2 大表分区（PG 优势能力，未来扩展）

文档量达百万级时，`knowledge_base` 与 `knowledge_permission` 启用**声明式分区**（按 company\_id 哈希分区），查询带公司条件自动分区裁剪。

### 4.3 Redis 缓存层



| 缓存        | key                  | 内容             | 失效时机             |
| --------- | -------------------- | -------------- | ---------------- |
| 用户权限上下文   | user:perm:{uid}      | 部门链、公司 ID、角色集合 | 部门 / 角色变更时       |
| 文档 ID 白名单 | user:docs:{uid}      | 可访问 doc\_id 集合 | 权限变更时按 kb\_id 失效 |
| 菜单权限      | role:menu:{role\_id} | 角色可访问菜单        | 授权变更时            |
| 热点文档      | kb:meta:{kb\_id}     | 文档元信息          | 更新时删除            |

> 检索顺序：Redis 白名单（命中直返）→ 未命中走 3.3 兜底单表查询 → 回填 Redis。

### 4.4 与 Qdrant 向量检索协同



* Qdrant 每个 chunk 的 payload 冗余 `doc_id`、`category_id`

* 权限在应用层 / Redis 白名单解决，Qdrant 只做向量相似度检索 + doc\_id 过滤（权限不依赖向量库过滤逻辑，双保险）

### 4.5 其他并发优化



* 读写分离：检索查询走只读副本（流复制）；上传 / 授权写主库

* 分页统一 `LIMIT pageSize` + 索引排序，禁止深分页 OFFSET（keyset 分页）

* 连接池：PgBouncer 或 ORM 连接池（SQLAlchemy pool），控制 max\_connections

* 异步任务由 Celery 队列削峰，避免上传高峰期拖垮主库

* 保持 autovacuum 开启，定期 `VACUUM ANALYZE`



***

## 5. 原文档未考虑项补充清单



| 补充项             | 说明                                                       |
| --------------- | -------------------------------------------------------- |
| 用户 - 角色多对多      | 原文档用户表无角色字段，新增 sys\_user\_role                           |
| 菜单定义表 sys\_menu | 原文档仅有关联表，菜单本身无法管理                                        |
| 知识库五级权限         | 原 knowledge\_base 无权限设计，V1.1 统一收敛到 knowledge\_permission |
| 物化路径 path       | 部门 / 分类树增加 path，免递归                                      |
| 公司冗余字段          | sys\_user.company\_id 冗余，免部门链递归取公司                       |
| 分类归属            | knowledge\_base 增加 category\_id（上传必填分类）                  |
| 解析 / 向量化任务表     | 异步任务状态可追踪、可重试                                            |
| 会话 / 消息表        | 聊天功能数据落库（AI 对话模块需要）                                      |
| 模型提供商表          | 新增 sys\_provider，支持配置多个模型提供商，聊天角色可绑定                    |
| 聊天角色表           | 新增 sys\_chat\_role，会话通过 chat\_role\_id 关联角色，先选角色才能建会话     |
| 消息角色枚举          | chat\_message.role 扩展为 0=系统 1=用户 2=助手 3=工具                  |
| 逻辑删除统一          | state=3，全部列表查询带 state 条件                                 |
| 时间字段统一          | create\_time /update\_time 全覆盖（PG 用 TIMESTAMP）           |
| 缓存与失效策略         | Redis 权限上下文 + 白名单，权限实时生效                                 |
| MinIO 文件存储      | file\_path 预留对象存储路径设计                                    |
| update\_time 维护 | PG 无 ON UPDATE，采用应用层维护（或触发器）                             |
| 索引精简            | knowledge\_base 只留 2 个必要索引，低写放大                          |



***

## 6. 后续可扩展（本期不做）



* 审计日志表（谁在何时改了谁的权限）

* 数据字典表（权限类型、状态枚举统一管理）

* 全文检索：PG 原生 `tsvector` + GIN 索引

* 部门表 nested-set（左右值）方案：部门树频繁整体迁移时才需要

* 只读副本 + 流复制承载高并发检索流量