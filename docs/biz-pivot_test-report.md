# 商枢 BizPivot 企业智能AI平台 —— 第三阶段测试报告

## 文档基础信息

| 项目名称 | 商枢 BizPivot 企业智能AI平台 |
| -------- | ---------------------------- |
| 文档名称 | 第三阶段测试报告（biz-pivot_test-report） |
| 测试范围 | 开发计划《development_plan.md》**阶段三：系统菜单初始化 + 后台管理（部门/用户/角色）** |
| 测试依据 | `docs/development_plan.md`、`docs/biz_pivot_prd.md`（5.2.1~5.2.3、3.1、9）、`docs/database_design.md`、`docs/api_spec.md`、`AGENTS.md` |
| 测试方式 | 静态代码审查 + 运行时接口冒烟测试 + 越权/边界用例（未修改任何业务代码） |
| 测试环境 | Windows + Python 3.13（.venv）+ Node v24.14.0 + Docker 依赖服务（PG15/Redis7.2/Qdrant/RabbitMQ3.13/Jaeger 均 Up） |
| 测试日期 | 2026-09-23 |
| 测试结论 | **阶段三主体目标达成，可进入阶段四；发现 2 项缺陷（1 项前端高优）+ 5 项偏差/待办** |

> 说明：本报告仅覆盖阶段三。阶段一/二测试报告见 git 历史；阶段二遗留项（A1/A2/A3/P2-U4）已在本阶段回归验证全部闭环（见第二节）。

---

## 一、测试结论摘要

| 结论项 | 状态 |
| ------ | ---- |
| 系统菜单初始化（8 条，state=0，code 正确回填） | ✅ 通过 |
| 部门无限级树（pid + path 物化路径，整树加载不分页） | ✅ 通过 |
| 部门新增/修改/删除（含更换父级 + 防循环嵌套） | ✅ 通过 |
| 部门删除校验（存在下级 / 归属用户禁止删除） | ✅ 通过 |
| 部门子树移动（path / company_id / is_company 同步重写） | ✅ 通过 |
| 用户分页列表（pageNum/pageSize，records/total/pages） | ✅ 通过 |
| 用户新增（归属部门必填 + 绑定角色多选） | ✅ 通过 |
| 用户编辑 / 删除 / 重置密码 / 启用禁用 | ✅ 通过 |
| 用户按账号 / 部门筛选（前端重置第 1 页） | ✅ 通过 |
| 角色分页列表 / 新增 / 修改 / 删除（校验用户绑定） | ✅ 通过 |
| 超级管理员不可删除 / 不可禁用（硬约束闭环） | ✅ 通过 |
| 越权拦截（未登录 401 / 普通用户 403 / pageSize>100 → 422） | ✅ 通过 |
| 阶段二遗留项 A1/A2/A3/P2-U4 回归 | ✅ 全部闭环 |
| 前端生产构建（`npm run build`） | ✅ 通过（仅 chunk>500kB 警告，非阻断） |
| **前端业务错误码（HTTP 200 + code!=0）未处理** | ❌ 缺陷（见 B2） |
| **软删除后重建同名账号/角色触发唯一冲突 500** | ❌ 缺陷（见 B1） |

---

## 二、阶段二遗留项回归

| 遗留项 | 阶段二描述 | 本阶段回归结果 |
| ------ | ---------- | -------------- |
| A1 | refresh token 可当 access token 使用 | ✅ 已修复。`core/auth.py:111` 新增 `decode_access_token`（强制 `type==access`），中间件（`auth_middleware.py:53`）与 `deps.py:42` 均已改用；`tests/test_auth.py` 步骤 5 验证 refresh token 访问受保护接口返回 401 |
| A2 | provider / chat-role 接口未挂超管校验 | ✅ 已修复。`provider.py`、`chat_role.py` 路由级 `dependencies=[Depends(require_super_admin)]`；`tests/test_auth.py` 步骤 9/10 验证普通用户返回 403 |
| A3 | 超管「不可删除/不可禁用」无硬约束 | ✅ 已闭环。`user_service.py:195` 删除拦截、`:215` 禁用拦截（`_is_super` 判定），实测均返回业务码 400 |
| P2-U4 | 菜单 `code` 未回填（沿用路由路径） | ✅ 已解决。`seed.py:75-77` 新增 code 回填逻辑；实测 8 条菜单 code 全部为正确权限标识（`dept:manage` 等） |

---

## 三、系统菜单初始化测试

实测 `sys_menu` 共 8 条（对齐 PRD 3.1 与数据库设计 V1.2），全部 `state=0`，code 与 page_type 正确：

| id | 名称 | path | code | page_type |
| -- | ---- | ---- | ---- | --------- |
| 1 | 部门管理 | /admin/dept | dept:manage | tree |
| 2 | 用户管理 | /admin/user | user:manage | list |
| 3 | 角色管理 | /admin/role | role:manage | list |
| 4 | 角色授权 | /admin/permission | permission:grant | list |
| 5 | 知识库分类 | /admin/category | category:manage | tree |
| 6 | 知识库上传 | /admin/knowledge | knowledge:upload | list |
| 7 | 模型提供商 | /admin/provider | provider:manage | list |
| 8 | 聊天角色 | /admin/chat-role | chat_role:manage | list |

> 说明：阶段三交付范围是前 6 条；第 7/8 条为阶段一底座菜单。`seed_menus` 幂等，缺失补插、code 不符回填（`seed.py:50-80`）。

---

## 四、部门管理测试（`/api/v1/dept`）

| 用例 | 期望 | 实测 | 结果 |
| ---- | ---- | ---- | ---- |
| `GET /dept/tree` 整树加载 | 树形结构、根为公司（is_company=1） | 200，根节点 `is_company=1` | ✅ |
| 新增顶级公司（pid=0） | is_company=1、company_id=自身、path=`/id/` | 正确 | ✅ |
| 新增子部门（pid=公司） | is_company=0、company_id=父公司 id、path 继承 | 正确 | ✅ |
| 修改部门（改名） | 名称更新 | 正确 | ✅ |
| 更换父级（防循环嵌套） | 移到自己/子孙下被拒绝 | 业务码 400（见 B2 前端不提示） | ✅ 后端正确 |
| 删除存在下级的部门 | 拒绝 | 业务码 400「存在下级部门」 | ✅ |
| 删除存在归属用户的部门 | 拒绝 | 业务码 400「存在归属用户」 | ✅ |
| 子树整体移动 | 子树 path/company_id/is_company 同步重写 | 实测 `/13/10/`、`/13/10/11/`、`/13/10/11/12/`，company_id=13 正确 | ✅ |

> 实现要点：`dept_service.py:72-93` 更换父级时先校验循环（`parent.path.startswith(dept.path)`），再用 `list_descendants` 重写整棵子树的 path/company_id。

---

## 五、用户管理测试（`/api/v1/user`）

| 用例 | 期望 | 实测 | 结果 |
| ---- | ---- | ---- | ---- |
| 分页列表（默认 pageNum=1/pageSize=10） | records/total/pages 结构 | 正确 | ✅ |
| pageSize 上限（>100） | 422 | 实测 pageSize=101 → 422 | ✅ |
| 新增用户（归属部门必填） | dept_id 必填，缺失返回 422 | 正确（schema `Field(...)`） | ✅ |
| 新增用户绑定角色（多选） | 写入 sys_user_role，返回 role_ids | 正确 | ✅ |
| 重复账号新增 | 409「登录账号已存在」 | 409 | ✅ |
| 归属部门不存在 | 404 | 404（`user_service.py:144`） | ✅ |
| 按账号筛选 | 模糊匹配 | 正确 | ✅ |
| 按部门筛选 | 精确 dept_id 匹配 | 正确 | ✅ |
| 修改用户（改部门时重算 company_id） | company_id 同步 | 正确（`user_service.py:175-179`） | ✅ |
| 重置密码 | 密码更新 + 会话失效 | 正确（改后旧会话失效，`clear_session`） | ✅ |
| 禁用账号 | state=1 + 会话失效 + 无法登录 | 禁用后登录返回 401「账号已被禁用」 | ✅ |
| 启用账号 | state=0 | 正确 | ✅ |
| 删除用户 | 软删除（state=3） | 正确 | ✅ |
| 删除超级管理员 | 拒绝 | 业务码 400「超级管理员不可删除」 | ✅ |
| 禁用超级管理员 | 拒绝 | 业务码 400「超级管理员不可禁用」 | ✅ |

> 实现要点：`user_service.py:209-220` `set_state` 校验状态值 ∈ {0,1}；禁用时 `clear_session` 使既有 Token 失效，符合「账号禁用彻底失效」。

---

## 六、角色管理测试（`/api/v1/role`）

| 用例 | 期望 | 实测 | 结果 |
| ---- | ---- | ---- | ---- |
| 分页列表 + keyword 筛选 | records/total/pages | 正确 | ✅ |
| `GET /role/all`（用户绑定下拉，不分页） | 全量列表 | 正确 | ✅ |
| 新增角色 | 名称唯一 | 正确 | ✅ |
| 重复角色名新增 | 409「角色名称已存在」 | 409 | ✅ |
| 修改角色（改名为已存在名） | 409 | 正确（`exclude_id` 排除自身） | ✅ |
| 删除已绑定用户的角色 | 拒绝 | 业务码 400「已绑定用户」 | ✅ |
| 删除无绑定角色 | 软删除 + 清 role:menu 缓存 | 正确（`perm.clear_role_menus`） | ✅ |

---

## 七、越权与边界测试

| 用例 | 期望 | 实测 | 结果 |
| ---- | ---- | ---- | ---- |
| 未登录访问 `/dept/tree`、`/user`、`/role` | 401 | 401 | ✅ |
| 普通登录用户访问后台管理接口 | 403「仅超级管理员」 | 403 | ✅ |
| pageSize=101 | 422 | 422 | ✅ |
| pageNum 越界（<1） | 422 | 422（`Query(ge=1)`） | ✅ |
| 状态值非法（set_state 传 3） | 业务码 400「状态值非法」 | 业务码 400 | ✅ |

---

## 八、前端测试

### 8.1 页面与构建

| 检查项 | 结果 |
| ------ | ---- |
| `views/admin/dept/index.vue` 无限级树（新增公司/添加子部门/编辑/删除） | ✅ |
| `views/admin/user/index.vue` 分页表格 + 账号/部门筛选 + 角色多选 + 重置密码 + 启停 | ✅ |
| `views/admin/role/index.vue` 分页表格 + keyword 搜索 + 启停 | ✅ |
| 筛选变更重置第 1 页（`onSearch`/`onReset`/`onSizeChange` 均 `pageNum=1`） | ✅ |
| `api/dept.js`、`api/user.js`、`api/role.js` 封装与后端接口对齐 | ✅ |
| `router/index.js` 阶段三页面路由注册 | ✅ |
| `npm run build` 生产构建 | ✅ 通过（5.33s；仅 chunk>500kB 警告） |

### 8.2 前端缺陷：业务错误码未处理（见 B2）

后端 `BizError` 统一返回 **HTTP 200 + code=400**（`core/exceptions.py:30-34`），而 `api/request.js:32` 的成功分支直接 `return response.data`，未判断 `code`。导致防循环嵌套、删除校验、超管不可删/禁等**业务失败**在前端被误报为「新增成功/修改成功/删除成功」。

---

## 九、缺陷与不一致清单

| 编号 | 级别 | 位置 | 问题描述 | 建议 |
| ---- | ---- | ---- | -------- | ---- |
| B1 | 中 | `repositories/user_repo.py:14-19`、`repositories/role_repo.py:42-46` + 唯一索引 `models/sys.py:38,62` | **软删除后重建同名账号/角色触发唯一约束冲突 500**。`get_by_account`/`get_by_name` 仅查询 `state != 删除`，重复校验通过；但 `uk_sys_user_account` / `uk_sys_role_name` 唯一索引不区分软删除，重建时 `INSERT` 触发 `IntegrityError` → 500「系统繁忙」。**实测复现（用户账号、角色名均 500）** | 三选一：① 唯一索引改为「部分唯一索引」`WHERE state != 3`（PostgreSQL 支持）；② 软删除时改写账号/名称为带后缀的已回收形式（如 `{原值}#del{id}`）；③ `get_by_account`/`get_by_name` 改为连同软删行一起查重并提示「账号/名称已被占用」 |
| B2 | 高 | `frontend/src/api/request.js:32-33` + 各管理页 `onSave/onDelete` | **前端未处理业务错误码（HTTP 200 + code!=0）**。后端 `BizError` 返回 HTTP 200，axios 走成功分支，页面无条件 `ElMessage.success`，导致「防循环嵌套/删除校验/超管不可删/禁」等失败被提示为成功 | 在 `request.js` 成功分支统一判断 `data.code`（如 `code !== 0 && code !== 200` 时 `ElMessage.error(data.message)` 并 `reject`）；或后端将业务错误改为非 200 状态码。建议前者，改动最小 |
| S1 | 中 | `repositories/user_repo.py:51`、`repositories/role_repo.py:36` | 分页采用 `offset().limit()`，与开发计划 6.5「分页统一 LIMIT（keyset），禁止深分页 OFFSET」不符 | 数据量不大时可延后；若坚持规范需改造为 keyset 分页（按上一页最后一条 id 作为游标） |
| S2 | 低 | `schemas/dept_schema.py:16` + `services/dept_service.py:43` | `DeptCreate.is_company` 入参被接受但被忽略（服务层按 `pid==0` 重算），易误导调用方 | 删除该入参，或加校验：`pid!=0` 时禁止 `is_company=1` |
| S3 | 低 | `services/user_service.py:143-145,176-179` | 创建/修改用户仅校验部门「已删除」，未校验「已禁用」；实测可将用户挂到禁用部门 | 是否允许挂禁用部门需产品确认；若不允许，补充 `state == STATE_DISABLED` 校验 |
| S4 | 低 | `services/user_service.py:191-199` | 删除用户仅软删，不清理 `sys_user_role` 关联行（`count_users` 已排除软删用户，故不影响角色删除，属数据卫生问题） | 软删除用户时同步删除其 `sys_user_role` 关联 |
| S5 | 低 | `frontend/src/App.vue` | 前端无侧边栏/导航菜单，部门/用户/角色等后台页面仅能通过 URL 直接访问 | 属阶段四「前端菜单动态展示」范畴，但阶段三交付时后台入口不可达；建议阶段四前临时补静态导航或确认延后 |

---

## 十、未完成项清单（供后续修改维护跟踪）

| 编号 | 类别 | 内容 | 归属阶段 | 说明 |
| ---- | ---- | ---- | -------- | ---- |
| P3-U1 | 缺陷 | B2：前端业务错误码未处理，业务失败误报成功 | 阶段三（应本阶段闭环） | 高优，影响所有后台管理页的错误反馈 |
| P3-U2 | 缺陷 | B1：软删除后重建同名账号/角色触发唯一冲突 500 | 阶段三 | 中优，需数据库唯一索引与查询逻辑对齐 |
| P3-U3 | 偏差 | S1：分页用 OFFSET，未按 6.5 keyset 规范 | 阶段三/后续 | 数据量小可延后 |
| P3-U4 | 偏差 | S2：DeptCreate.is_company 入参被忽略 | 阶段三 | 接口契约需与实现对齐 |
| P3-U5 | 偏差 | S3：用户可挂到「禁用」部门 | 阶段三 | 需产品确认规则 |
| P3-U6 | 偏差 | S4：删除用户未清理 sys_user_role 关联 | 阶段三 | 数据卫生，可顺手处理 |
| P3-U7 | 待办 | S5：前端无导航菜单，后台页面仅 URL 可达 | 阶段四 | 随菜单动态展示一并实现 |
| P3-U8 | 遗留 | 「删除用户前校验关联数据」（chat_session/knowledge 等） | 阶段五/六 | 相关模块未落地，暂不适用 |

---

## 十一、需要人工确认的事项（含具体步骤）

### 11.1 后台管理 UI 全流程人工验证

> 注意：当前前端**无侧边栏菜单**，需手动在地址栏输入路由。

1. 启动后端：`cd backend` 后 `& "..\.venv\Scripts\python.exe" -m uvicorn app.main:app --reload --port 8000`。
2. 启动前端：`cd frontend` 后 `npm run dev`，浏览器打开 `http://localhost:5173`。
3. 用 `admin / Admin@123` 登录，浏览器地址栏依次访问：
   - `http://localhost:5173/admin/dept`（部门管理）
   - `http://localhost:5173/admin/user`（用户管理）
   - `http://localhost:5173/admin/role`（角色管理）
4. 部门页：新增公司 → 新增子部门 → 编辑改名 → 尝试删除有下级的部门（**观察：因 B2 缺陷，预期会误提示「删除成功」，但刷新树仍存在**）。
5. 用户页：新增用户（选部门、选角色）→ 搜索账号 → 禁用 → 用该账号登录确认被拒 → 启用 → 重置密码。
6. 角色页：新增角色 → 编辑 → 删除空角色 → 删除已绑定用户的角色（**同样受 B2 影响，误提示成功**）。
7. 打开 DevTools → Network，观察业务失败请求返回 `200`，响应体为 `{"code":400,"message":...}`（B2 根因）。

### 11.2 缺陷 B1 修复方案确认

需开发确认采用哪种方案：
- **方案 A（推荐）**：`uk_sys_user_account`、`uk_sys_role_name` 改为 PostgreSQL 部分唯一索引（`CREATE UNIQUE INDEX ... WHERE state != 3`），并移除 ORM 里的 `Index(..., unique=True)` 改为普通索引 + 迁移脚本。
- **方案 B**：软删除时改写账号/名称（如追加 `#del{id}`），释放唯一键位。

确认后可要求我补充对应的数据库迁移/回填脚本验证步骤。

### 11.3 缺陷 B2 修复方案确认

需确认前端统一拦截业务错误码的位置：建议在 `api/request.js` 成功分支判断 `data.code`，非 0/200 时 `ElMessage.error(data.message)` 并 `reject`。需确认后端约定：业务成功是否也返回 `code`（当前部分接口返回裸 `{"message":...}`，部分返回 `{code,message,data}`），统一后前端判断逻辑才稳定。

### 11.4 S3 规则确认

需产品确认：是否允许用户归属到「已禁用」部门。若不允许，后端需补充禁用部门校验；若允许，需明确禁用部门的语义（是否仅影响展示）。

---

## 十二、附录：本次测试关键执行命令

```powershell
# 工作目录 backend，使用项目 .venv
& "..\.venv\Scripts\python.exe" -m tests.test_auth     # 阶段二回归（A1/A2 已闭环）
& "..\.venv\Scripts\python.exe" -m tests.test_admin    # 阶段三冒烟（9 步，全部通过）

# 越权/边界用例（临时脚本，未改动仓库代码）
#   - 超管删除/禁用拦截、pageSize=101→422、软删重建唯一冲突(B1)、
#     is_company 忽略(S2)、禁用部门挂用户(S3)、子树移动 path 重写 —— 均实测
& "..\.venv\Scripts\python.exe" "<temp>\phase3_edge.py"
& "..\.venv\Scripts\python.exe" "<temp>\phase3_edge2.py"
& "..\.venv\Scripts\python.exe" "<temp>\phase3_move.py"

# 菜单种子核对（8 条 + code 回填）
& "..\.venv\Scripts\python.exe" -c "import sys; sys.path.insert(0,'.'); ..."

# 前端生产构建
npm run build        # 5.33s，通过；仅 chunk>500kB 警告

# 依赖服务状态
docker ps            # pg-biz / redis / qdrant / rabbitmq / jaeger 均 Up
```

> 注：本报告仅覆盖阶段三，未修改任何源代码。测试产生的临时数据已通过清理脚本物理移除（`<temp>` 为 `C:\Users\user\AppData\Local\Temp\opencode`）。
