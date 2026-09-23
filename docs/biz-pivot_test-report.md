# 商枢 BizPivot 企业智能AI平台 —— 第二阶段测试报告

## 文档基础信息

| 项目名称 | 商枢 BizPivot 企业智能AI平台 |
| -------- | ---------------------------- |
| 文档名称 | 第二阶段测试报告（biz-pivot_test-report） |
| 测试范围 | 开发计划《development_plan.md》**阶段二：登录鉴权体系 + 内置超级管理员** |
| 测试依据 | `docs/development_plan.md`、`docs/database_design.md`、`docs/biz_pivot_prd.md`、`AGENTS.md` |
| 测试方式 | 静态代码审查 + 运行时接口冒烟测试 + 越权/边界用例（不修改任何代码） |
| 测试环境 | Windows + Python 3.13（.venv）+ Node v24.14.0 + Docker 依赖服务（PG15/Redis7.2/Qdrant/RabbitMQ3.13/Jaeger 均 Up） |
| 测试日期 | 2026-09-23 |
| 测试结论 | **阶段二主体目标达成，可进入阶段三；发现 1 项安全缺陷 + 2 项需在后续阶段落地/对齐的未完成项** |

> 说明：本报告仅覆盖阶段二（登录鉴权 + 内置超级管理员）。阶段一测试报告此前已完成，本文件为阶段二测试报告（阶段一内容可通过 git 历史找回）。

---

## 一、测试结论摘要

| 结论项 | 状态 |
| ------ | ---- |
| 登录接口（`POST /api/v1/auth/login`）统一入口 | ✅ 通过 |
| 密码加密存储（PBKDF2 + pwd/slot 加盐） | ✅ 通过 |
| 错误密码 / 不存在账号 → 401 友好提示 | ✅ 通过 |
| 禁用账号禁止登录（「账号已被禁用」） | ✅ 通过 |
| 禁用账号既有 Token 彻底失效（请求级实时校验） | ✅ 通过 |
| Token 生成 / 刷新 / 登出闭环 + Redis 会话 | ✅ 通过 |
| 全局鉴权拦截中间件（未登录一律 401） | ✅ 通过 |
| `api/deps.py` 依赖注入（当前用户 / 超管拦截器） | ✅ 通过 |
| 内置超级管理员唯一 + 幂等种子 | ✅ 通过 |
| 前端登录页 + 路由守卫 + 401 自动刷新 | ✅ 通过 |
| refresh token 与 access token 类型隔离 | ❌ 缺陷（见 A1） |
| provider / chat-role 接口超管专属校验 | ⚠️ 未落地（阶段四，见 A2） |
| 超管「不可删除/不可禁用」硬约束 | ⚠️ 未落地（阶段三，见 A3） |

---

## 二、鉴权核心链路测试

### 2.1 登录接口

| 用例 | 期望 | 实测 | 结果 |
| ---- | ---- | ---- | ---- |
| 超管正确登录 `admin/Admin@123` | 200 返回 access+refresh+user | 200，含 `access_token`/`refresh_token`/`user` | ✅ |
| 登录返回 user 不含密码字段 | 不泄露 `pwd`/`slot` | 返回 `UserOut` 无敏感字段 | ✅ |
| 错误密码登录 | 401「账号或密码错误」 | 401 | ✅ |
| 不存在账号登录 | 401 | 401 | ✅ |
| 禁用账号登录 | 401「账号已被禁用」 | 401，提示含「禁用」 | ✅ |

### 2.2 刷新 / 登出 / 资料

| 用例 | 期望 | 实测 | 结果 |
| ---- | ---- | ---- | ---- |
| 携带 refresh_token 刷新 | 200，轮换新 token 并更新会话 | 200 | ✅ |
| 登出后 access token 访问受保护接口 | 401（会话已清） | 401 | ✅ |
| 登出后 refresh token 再刷新 | 401（refresh 已失效） | 401 | ✅ |
| `GET /auth/profile` 携带有效 token | 200 返回当前用户 | 200 | ✅ |

### 2.3 密码加密（`core/auth.py`）

- ✅ `hash_password` 采用 stdlib PBKDF2-HMAC-SHA256（100,000 次迭代），`slot` 为 16 字节随机 hex。
- ✅ `verify_password` 使用 `hmac.compare_digest` 恒定时间比较，防时序攻击。
- ✅ `make_password` 返回 `(slot, pwd_hash)`，与 `sys_user` 表结构对齐。

---

## 三、全局鉴权拦截中间件测试（`core/auth_middleware.py`）

| 用例 | 期望 | 实测 | 结果 |
| ---- | ---- | ---- | ---- |
| 无 Token 访问受保护接口 | 401 | 401 | ✅ |
| 畸形 Token（`Bearer bad.token.here`） | 401 | 401 | ✅ |
| 过期 Token | 401「登录已过期」 | 401（decode 抛 UnauthorizedError） | ✅ |
| 错误签发方（issuer 不符）Token | 401 | 401 | ✅ |
| 白名单 `/auth/login`、`/auth/refresh`、`/system/health` | 无需登录 | 正常放行 | ✅ |
| 非白名单 `/system/info`、`/system/constants` 未登录 | 401 | 401 | ✅ |
| 根路由 `/`（非 `/api/v1` 前缀） | 公开 | 200 | ✅ |
| CORS 预检 OPTIONS | 放行 | 放行（中间件首行判断） | ✅ |

> 校验链：解析 Bearer → Redis `session_exists` → 数据库实时校验账号状态（禁用/删除），三层齐全。

---

## 四、禁用账号彻底失效测试（越权重点）

| 场景 | 期望 | 实测 | 结果 |
| ---- | ---- | ---- | ---- |
| 登录后账号被置为 `state=1`（禁用） | 既有 access token 下一次请求即 401 | 401（中间件请求级重查 DB） | ✅ |
| 禁用账号重新登录 | 401「账号已被禁用」 | 401 | ✅ |
| 禁用账号访问受保护接口（复用旧 token） | 401 | 401 | ✅ |

> 关键：`AuthMiddleware.dispatch` 每次请求都用 `SessionLocal` 重新读取 `SysUser.state`，因此禁用**即时生效**，而非依赖 Token 过期，符合 PRD「禁用账号彻底失效」。

---

## 五、Token 与安全专项测试

| 检查项 | 结果 |
| ------ | ---- |
| JWT 载荷含 `sub/account/is_super/type/iat/exp/iss` | ✅ |
| access 与 refresh 使用不同有效期（720min / 43200min） | ✅ |
| `decode_token` 校验 issuer 与算法 | ✅ |
| `decode_refresh_token` 校验 `type==refresh` | ✅ |
| 会话 TTL = refresh token 有效期，外置 Redis | ✅ |
| 登出/刷新主动失效会话 | ✅ |
| **access 与 refresh 类型隔离（中间件/依赖层强制）** | ❌ 见缺陷 A1 |

---

## 六、内置超级管理员测试

| 检查项 | 结果 |
| ------ | ---- |
| 启动自动创建超管（幂等） | ✅ |
| 超管账号唯一（DB 计数 = 1） | ✅ |
| 超管 `is_super` 判定（`account == settings.super_admin_account`） | ✅ |
| `require_super_admin` 拦截器存在（`api/deps.py`） | ✅ 已实现但尚未挂到 provider/chat-role（见 A2） |
| 「不可删除 / 不可禁用」硬约束 | ⚠️ 见 A3 |

---

## 七、前端登录与鉴权状态测试

| 检查项 | 结果 |
| ------ | ---- |
| `views/login/index.vue` 真实登录表单（账号+密码+回车登录） | ✅ |
| 登录成功写入 Pinia + localStorage（token/refresh/user） | ✅ |
| `router.beforeEach` 未登录跳转 `/login` 并带 `redirect` | ✅ |
| `api/request.js` 401 自动 refresh + 并发队列 + 刷新失败登出 | ✅ |
| `api/auth.js` 封装 login/refresh/logout/profile | ✅ |
| `npm run build` 生产构建 | ✅ 通过（2253 模块，5.32s；仅 chunk>500kB 警告，非阻断） |

---

## 八、缺陷与不一致清单

| 编号 | 级别 | 位置 | 问题描述 | 建议 |
| ---- | ---- | ---- | -------- | ---- |
| A1 | 中 | `core/auth_middleware.py:53`、`api/deps.py:42` | **refresh token 可当作 access token 直接访问受保护接口**。两处均调用 `auth_core.decode_token`（不校验 `type` 字段），而 refresh token 有效期为 43200 分钟（30 天），远长于 access token（720 分钟）。实测携带 refresh token 访问 `/auth/profile` 返回 200 | 在鉴权层强制类型隔离：中间件与 `get_current_user` 改用带 `expected_type="access"` 的解码（或新增 `decode_access_token`），拒绝 refresh token 作为访问凭证 |
| A2 | 中 | `api/v1/provider.py`、`api/v1/chat_role.py` | 模型提供商 / 聊天角色增删改接口目前**仅要求已登录**，未挂 `require_super_admin`，任何普通员工登录后均可增删改提供商与聊天角色（代码注释已标注「阶段二后需追加」） | 阶段四角色授权落地时，为这两个模块的 POST/PUT/DELETE 追加 `Depends(require_super_admin)`；阶段二期间属于已知风险，需排期闭环 |
| A3 | 低 | `models/seed.py:126` | 超管「不可删除、不可禁用」目前无硬约束：seed 仅「存在则跳过」，尚无用户管理 API 兜底（阶段三才有用户 CRUD） | 阶段三用户管理接口落地时，对 `account == super_admin_account` 的用户禁止删除与禁用（后端硬校验） |

---

## 九、未完成项清单（供后续修改维护跟踪）

| 编号 | 类别 | 内容 | 归属阶段 | 说明 |
| ---- | ---- | ---- | -------- | ---- |
| P2-U1 | 缺陷 | A1：refresh token 类型隔离未在鉴权层强制 | 阶段二（应本阶段闭环） | 建议优先修复，安全相关 |
| P2-U2 | 风险 | A2：provider/chat-role 接口超管专属校验未挂载 | 阶段四 | `require_super_admin` 已就绪，仅需路由层挂载 |
| P2-U3 | 风险 | A3：超管不可删除/禁用无硬约束 | 阶段三 | 依赖用户管理 CRUD 落地时一并实现 |
| P2-U4 | 遗留 | 菜单 `code` 未回填（阶段一 D2 残留） | 阶段四 | 现网 DB 中前 6 条菜单 `code` 仍为路由路径（如 `/admin/dept`），`seed_menus` 按 path 幂等跳过、不更新已有 code；仅新增的 provider/chat-role 两条 code 正确。影响阶段四授权判定，需提供一次性回填脚本或调整 seed 更新逻辑 |
| P2-U5 | 备注 | `get_current_user` 不校验会话存在性（依赖中间件先行拦截） | — | 功能正确但属单点依赖，建议后续做纵深防御时补一层会话校验 |

---

## 十、需要人工确认的事项（含具体步骤）

### 10.1 浏览器登录 UI 全流程验证

1. 启动后端：`cd backend` 后 `& "..\.venv\Scripts\python.exe" -m uvicorn app.main:app --reload --port 8000`。
2. 启动前端：`cd frontend` 后 `npm run dev`，浏览器打开 `http://localhost:5173`。
3. 未登录访问 `/chat`，确认被守卫重定向到 `/login?redirect=/chat`。
4. 输入 `admin / Admin@123` 点击「登录」，确认跳转 `/chat`，右上角显示「超级管理员」与健康标签「服务正常」。
5. 输入错误密码，确认页面顶部出现「账号或密码错误」提示，不跳转。
6. 点击右上角「退出登录」，确认回到 `/login`，再次访问 `/chat` 仍被拦截。
7. 打开浏览器 DevTools → Network，确认登录请求 Header 携带 `Authorization: Bearer ...`，401 时自动触发一次 `/auth/refresh` 并重放原请求。

### 10.2 禁用账号彻底失效的人工验证

1. 用 `admin` 登录后，在数据库执行：`UPDATE sys_user SET state=1 WHERE account='__test__';`（先自行创建该测试账号，或直接对某个非超管账号操作）。
2. 该账号若已持有登录会话，刷新页面或请求任意接口，确认返回 401 并被强制登出。
3. 用该禁用账号重新登录，确认提示「账号已被禁用」。
4. 验证完成后将账号 `state` 恢复为 0。

### 10.3 缺陷 A1 的取舍确认

需开发确认：是否在阶段二立即修复「refresh token 可作 access token 使用」问题。若认可，建议方案为在 `core/auth.py` 新增 `decode_access_token`（校验 `type == access`），并在 `AuthMiddleware` 与 `deps.get_current_user` 中替换现有 `decode_token` 调用。

### 10.4 缺陷 A2 的排期确认

需产品/开发确认：阶段二~四期间，模型提供商、聊天角色两个后台模块是否允许普通登录用户操作。若不允许，应在阶段四前临时追加 `require_super_admin` 依赖兜底。

---

## 十一、附录：本次测试关键执行命令

```powershell
# 工作目录 backend，使用项目 .venv
& "..\.venv\Scripts\python.exe" -m tests.test_auth          # 阶段二鉴权冒烟（9 步，全部通过）

# 越权/边界用例（15 项，1 项失败 -> 缺陷 A1）
& "..\.venv\Scripts\python.exe" "<temp>\phase2_edge.py"

# Token 有效期 / issuer 校验 + 数据库种子计数
& "..\.venv\Scripts\python.exe" -c "import app.core.auth as a; ..."

# 前端生产构建
npm run build

# 依赖服务状态
docker ps   # pg-biz / redis / qdrant / rabbitmq / jaeger 均 Up
```

> 注：本报告仅覆盖阶段二，未修改任何源代码。数据库初始化/种子为幂等操作，与系统启动时 `AUTO_INIT_DB=true` 行为一致。
