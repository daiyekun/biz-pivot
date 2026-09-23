# 商枢 BizPivot 企业智能AI平台 —— 第四阶段测试报告

## 文档基础信息

| 项目名称 | 商枢 BizPivot 企业智能AI平台 |
| -------- | ---------------------------- |
| 文档名称 | 第四阶段测试报告（biz-pivot_test-report） |
| 测试范围 | 开发计划《development_plan.md》**阶段四：角色授权（菜单权限树 + 知识库权限配置）** |
| 测试依据 | `docs/development_plan.md`、`docs/biz_pivot_prd.md`（3.2、4.1、5.2.4、7.4、9）、`docs/database_design.md`（2.5/2.6、4.3）、`docs/api_spec.md`（§6）、`AGENTS.md` |
| 测试方式 | 静态代码审查 + 运行时接口冒烟测试 + 越权/边界用例（未修改任何业务代码） |
| 测试环境 | Windows + Python 3.13（.venv）+ Node v24 + Docker 依赖服务（PG15/Redis7.2/Qdrant/RabbitMQ3.13/Jaeger 均 Up） |
| 测试日期 | 2026-09-23 |
| 测试结论 | **阶段四主体目标达成（菜单授权/动态菜单/权限判定闭环）；发现 1 项高优偏差（后台菜单授权「可见不可用」）+ 1 项未完成项（知识库可访问分类范围）+ 1 项文档漂移** |

> 说明：本报告仅覆盖阶段四，未修改任何源代码。阶段三遗留缺陷（B1/B2/S4）已在本阶段回归验证全部闭环（见第二节）。测试产生的临时数据已在脚本内自清理。

---

## 一、测试结论摘要

| 结论项 | 状态 |
| ------ | ---- |
| 菜单权限树 `GET /menu/tree`（整树不分页，仅超管） | ✅ 通过 |
| 角色已授权菜单 `GET /menu/role/{role_id}`（仅超管） | ✅ 通过 |
| 保存角色菜单授权 `PUT /menu/role/{role_id}`（全量覆盖 + 去重 + 空数组清空） | ✅ 通过 |
| 非法菜单 ID 授权 → 404 拒绝 | ✅ 通过 |
| 动态菜单 `GET /menu/mine`（超管全量 / 普通用户按授权过滤） | ✅ 通过 |
| 授权变更即时刷新 `role:menu:{role_id}` 缓存（保存即时生效） | ✅ 通过 |
| 登录时预热角色菜单缓存（`deps.py` warm_role_menus） | ✅ 通过 |
| 后端权限判定 `core/permission.py`（has_menu / has_upload / has_category） | ✅ 通过 |
| 越权拦截（普通用户访问 menu/tree、menu/role → 403） | ✅ 通过 |
| 前端角色授权页面（角色分页+搜索、菜单树勾选、知识库权限开关） | ✅ 通过 |
| 前端动态菜单（`App.vue` 未授权菜单隐藏） | ✅ 通过 |
| 前端生产构建（`npm run build`） | ✅ 通过 |
| 阶段三遗留 B1（软删重建唯一冲突）/B2（业务码未处理）/S4（删用户未清关联） | ✅ 全部闭环 |
| **后台管理菜单授权「可见但不可用」（授权后接口仍 403）** | ❌ 偏差（见 D1） |
| **知识库权限配置「可访问的知识库分类范围」未实现** | ❌ 未完成（见 D2） |

---

## 二、阶段三遗留项回归（与阶段四相关）

阶段四角色授权页面依赖 `request.js` 正确处理业务错误，且授权/角色删除依赖软删除释放唯一键，故对以下遗留项做回归：

| 遗留项 | 阶段三描述 | 本阶段回归结果 |
| ------ | ---------- | -------------- |
| B1 | 软删除后重建同名账号/角色触发唯一冲突 500 | ✅ 已修复。`role_repo.py:62-71` 与 `user_repo.py:77-87` 软删时改写 name/account 为 `{原值}__del_{id}` 释放唯一键；测试菜单授权链路中的建角色/删角色/重建均正常 |
| B2 | 前端未处理业务错误码（HTTP 200 + code!=0）误报成功 | ✅ 已修复。`request.js:37-40` 成功分支判断 `data.code !== 0` 时 `ElMessage.error` 并 `reject`；角色授权页保存失败不会再误报成功 |
| S4 | 删除用户未清理 sys_user_role 关联 | ✅ 已修复。`user_repo.py:81` 软删时同步删除 `SysUserRole` 关联行 |

---

## 三、菜单授权接口测试（`/api/v1/menu`）

冒烟测试 `tests/test_menu.py` 11 步全部通过（见附录命令），关键用例：

| 用例 | 期望 | 实测 | 结果 |
| ---- | ---- | ---- | ---- |
| `GET /menu/tree` 整树 | 树形结构、含 8 条菜单、code 正确 | 200，8 条菜单，`knowledge:upload`/`category:manage` 等 code 存在 | ✅ |
| `GET /menu/role/{role_id}`（新建角色） | 初始 menu_ids=[] | 200，`menu_ids == []` | ✅ |
| `PUT /menu/role/{role_id}` 保存授权 | 写入 sys_menu_function，返回 menu_ids | 200，去重后返回正确集合 | ✅ |
| 授权非法菜单 ID（999999） | 404「菜单不存在」 | 404 | ✅ |
| 回读授权 | 与保存一致 | 200，一致 | ✅ |
| 清空授权（menu_ids=[]） | 全量删除授权 | 200，随后 `/menu/mine` 返回空 | ✅ |
| `GET /menu/mine`（普通用户） | 仅返回授权菜单路径 | 授权 knowledge/category → 返回 `/admin/knowledge`、`/admin/category`，不含 dept/user | ✅ |
| `GET /menu/mine`（超管） | 返回全部菜单路径 | 全部 8 条 | ✅ |

> 实现要点：`menu_service.py:46-58` 保存时去重 + 校验非法 ID + 全量覆盖写入 + 即时 `perm.cache_role_menus` 刷新缓存；`menu_repo.py:57-62` `replace_role_menus` 先删后插事务提交。

---

## 四、后端权限判定与缓存测试（`core/permission.py`）

| 用例 | 期望 | 实测 | 结果 |
| ---- | ---- | ---- | ---- |
| `has_upload_permission(ctx)`（授权 knowledge:upload） | True | True | ✅ |
| `has_category_permission(ctx)`（授权 category:manage） | True | True | ✅ |
| `has_menu_permission(ctx, "knowledge:upload")` | True | True | ✅ |
| `has_menu_permission(ctx, "dept:manage")`（未授权） | False | False | ✅ |
| 超管 `has_*` 全部返回 True | True | True（`is_super` 短路） | ✅ |
| 角色删除后清 `role:menu:{role_id}` 缓存 | 缓存清除 | `role_service.py:52` `perm.clear_role_menus` | ✅ |

> 实现要点：`permission.py:106-116` `_role_has_menu` 每次请求实时读 Redis 缓存，授权变更 `save_role_menus` 即时刷新，保证后端二次拦截实时生效；`deps.py:76-79` 登录时 `warm_role_menus` 预热缓存（缺失才查库）。

---

## 五、越权与边界测试

| 用例 | 期望 | 实测 | 结果 |
| ---- | ---- | ---- | ---- |
| 未登录访问 `/menu/tree`、`/menu/mine` | 401 | 401 | ✅ |
| 普通登录用户访问 `/menu/tree`（仅超管） | 403 | 403 | ✅ |
| 普通登录用户访问 `/menu/role/{role_id}`（仅超管） | 403 | 403 | ✅ |
| 授权不存在的角色 → 保存 | 404「角色不存在」 | `_ensure_role` 拦截 | ✅ |
| 授权已软删角色 → 保存 | 404 | `_ensure_role` 校验 `STATE_DELETED` | ✅ |

---

## 六、前端测试

### 6.1 页面与构建

| 检查项 | 结果 |
| ------ | ---- |
| `views/admin/permission/index.vue` 角色选择列表（分页 + keyword 搜索 + 重置第 1 页） | ✅ |
| 菜单权限树（`el-tree` show-checkbox、default-expand-all、整树不分页） | ✅ |
| 知识库权限配置区（knowledge:upload / category:manage 开关） | ✅ |
| 保存时合并 `getCheckedKeys + getHalfCheckedKeys` 去重提交 | ✅ |
| `api/menu.js` 封装与后端接口对齐（tree/role/mine/saveRoleMenus） | ✅ |
| `App.vue` 动态菜单：`adminMenus` 按 `userStore.isSuper || menuPaths.includes(path)` 过滤 | ✅ |
| `router/index.js` 阶段四「角色授权」路由注册（`/admin/permission`） | ✅ |
| `npm run build` 生产构建 | ✅ 通过（5.41s；仅 chunk>500kB 警告，非阻断） |

### 6.2 前端路由层未做菜单级拦截（低）

`router/index.js:79-86` `beforeEach` 仅校验 `isLoggedIn`，未校验目标路由是否在授权菜单内。普通用户手动输入 `/admin/dept` 等未授权路由 URL 时，页面仍会加载（依赖后端 403 兜底）。属「前端隐藏」之外的 URL 直达场景，后端已拦截，风险低。

---

## 七、缺陷与不一致清单

| 编号 | 级别 | 位置 | 问题描述 | 建议 |
| ---- | ---- | ---- | -------- | ---- |
| D1 | 高（待确认） | `api/v1/dept.py:21`、`api/v1/user.py:32`、`api/v1/role.py:24`（router 级 `require_super_admin`）vs `core/permission.py` 的 `require_menu_permission` | **后台管理菜单授权「可见但不可用」**。普通角色被授权 `dept:manage`/`user:manage` 后，`GET /menu/mine` 返回 `/admin/dept`、`/admin/user`（前端侧边栏会显示这些菜单），但 `/dept/tree`、`/user`、`/role` 等接口仍走 `require_super_admin` → **403**。即「角色 → 菜单功能权限闭环（前端隐藏 + 后端拦截双层）」对部门/用户/角色/角色授权等后台菜单未真正生效，仅对知识库权限（category:manage / knowledge:upload，阶段六生效）有意义。**已实测复现**：授权 `dept:manage`+`user:manage` 后 `/menu/mine` 返回对应路径，但 `/dept/tree`、`/user`、`/role` 均 403 | 需产品/开发确认后台管理菜单的授权语义二选一：① 若后台管理菜单应可授权给普通角色，则将 dept/user/role/permission 的 `require_super_admin` 改为 `require_menu_permission(MENU_CODE_*)`（provider/chat-role 同理）；② 若后台管理仅超管专属，则应从「菜单权限树」中剔除部门/用户/角色/角色授权，只保留知识库分类/知识库上传等可授权项，避免「授权了却不可用」的误导 |
| D2 | 中（未完成） | `views/admin/permission/index.vue:134-137` + `schemas/permission_schema.py`（空）+ 后端无对应接口/模型 | **知识库权限配置「可访问的知识库分类范围」未实现**。开发计划阶段四第 3 点与 PRD 5.2.4/7.4 均要求「为角色分配知识库上传/管理权限，以及**可访问的知识库分类范围**」，但前端仅有 `knowledge:upload`、`category:manage` 两个开关，无分类范围选择；后端无角色→分类授权数据模型/接口（`permission_schema.py` 为空） | 需确认归属：若「可访问分类范围」属阶段六（`knowledge_permission` 明细表 + 五级数据权限）范畴，则应在阶段四报告中标注为「阶段六落地」，并在页面预留提示；若属阶段四，需补充角色→分类授权表/接口与前端分类范围选择组件 |
| D3 | 低（文档漂移） | `docs/database_design.md` §2.5 `sys_menu` | 数据库设计文档 `sys_menu` 表字段清单缺 `code`、`page_type` 两列（实现模型 `models/sys.py:82-96` 与 `constants.MENU_SEEDS` 均有），而 `code` 是阶段四权限判定的**核心标识**，文档缺失易误导后续维护 | 同步更新数据库设计文档 §2.5 字段清单，补齐 `code`（VARCHAR(50)）、`page_type`（VARCHAR(20)） |

---

## 八、未完成项清单（供后续修改维护跟踪）

| 编号 | 类别 | 内容 | 归属阶段 | 说明 |
| ---- | ---- | ---- | -------- | ---- |
| P4-U1 | 偏差 | D1：后台管理菜单授权「可见不可用」，部门/用户/角色/角色授权等接口仍超管专属 | 阶段四（应本阶段闭环或明确规则） | 高优，需产品确认后台管理菜单是否可授权普通角色 |
| P4-U2 | 未完成 | D2：知识库权限配置「可访问的知识库分类范围」未实现 | 阶段四或阶段六（待确认归属） | 中优，涉及角色→分类授权数据模型 |
| P4-U3 | 文档 | D3：数据库设计文档 `sys_menu` 缺 `code`/`page_type` 字段 | 阶段四/文档维护 | 低优，同步文档即可 |
| P4-U4 | 待落地 | `require_menu_permission`/`require_upload_permission`/`require_category_permission` 依赖已就绪，但 `category.py`、`rag.py` 为空文件，当前无路由挂载 | 阶段六 | 属正常（阶段六 RAG 落地时使用），记录以明确交付边界 |
| P4-U5 | 低 | 前端路由层未做菜单级拦截（`router/index.js` 仅校验登录态） | 阶段四/后续 | 未授权 URL 直达时页面加载、后端 403 兜底，风险低 |

---

## 九、需要人工确认的事项（含具体步骤）

### 9.1 缺陷 D1 修复方案确认（后台菜单授权语义）

需产品/开发确认二选一，并据此调整：

- **方案 A（后台菜单可授权普通角色）**：将 `dept.py`/`user.py`/`role.py`（及 `provider.py`/`chat_role.py`）的 router 级 `require_super_admin` 改为 `require_menu_permission(constants.MENU_CODE_*)`，保留超管全量权限。验证：普通角色授权「部门管理」后，`/menu/mine` 含 `/admin/dept` 且 `GET /dept/tree` 返回 200；撤销授权后返回 403。
- **方案 B（后台管理仅超管专属）**：菜单权限树仅保留可授权项（知识库分类/知识库上传），部门/用户/角色/角色授权不作为可勾选项，避免「授权却不可用」的误导。

### 9.2 缺陷 D2 归属确认（可访问分类范围）

需确认「可访问的知识库分类范围」是否属阶段六（`knowledge_permission` 五级数据权限落地）范畴。若属阶段六，建议阶段四页面在「知识库权限配置」区增加说明文字「分类访问范围将在知识库模块（阶段六）配置」；若属阶段四，需补充角色→分类授权表与接口。

### 9.3 后台授权 UI 全流程人工验证（具体步骤）

1. 启动后端：`cd backend` 后 `& "..\.venv\Scripts\python.exe" -m uvicorn app.main:app --reload --port 8000`。
2. 启动前端：`cd frontend` 后 `npm run dev`，浏览器打开 `http://localhost:5173`。
3. 用 `admin / Admin@123` 登录，侧边栏进入【角色授权】`http://localhost:5173/admin/permission`。
4. 新建一个测试角色（`http://localhost:5173/admin/role`），回到【角色授权】左侧选择该角色。
5. 勾选「知识库分类」「知识库上传」菜单，保存 → 观察「授权保存成功」提示。
6. 新建一个绑定该角色的普通用户，用该用户登录 → 侧边栏应仅显示【知识库分类】【知识库上传】（未授权菜单隐藏）。
7. 该普通用户点击【知识库分类】→ 因阶段六未落地，接口为空壳，预期页面为空或后端 404/未实现（属阶段六，非本阶段缺陷）。
8. 回到超管，为角色勾选「部门管理」并保存，普通用户刷新 → 侧边栏出现【部门管理】，但进入页面所有接口返回 403（**即 D1 缺陷，需人工确认修复方案**）。
9. DevTools → Network 观察：业务失败返回 `{"code":403,"message":"仅超级管理员可执行该操作"}`，前端已正确弹出错误提示（B2 已修复）。

---

## 十、附录：本次测试关键执行命令

```powershell
# 工作目录 backend，使用项目 .venv
& "..\.venv\Scripts\python.exe" -m tests.test_menu    # 阶段四冒烟（11 步，全部通过）

# 越权/边界用例（临时脚本，未改动仓库代码）
#   - 普通角色授权 dept:manage+user:manage 后 /menu/mine 返回路径，但 /dept/tree、/user、/role 均 403（复现 D1）
& "..\.venv\Scripts\python.exe" "C:\Users\user\AppData\Local\Temp\opencode\phase4_edge.py"

# 前端生产构建
npm run build        # 5.41s，通过；仅 chunk>500kB 警告

# 依赖服务状态
docker ps            # pg-biz / redis / qdrant / rabbitmq / jaeger 均 Up
```

> 注：本报告仅覆盖阶段四，未修改任何源代码。测试产生的临时数据（测试角色/用户）已由测试脚本自清理；临时脚本位于 `C:\Users\user\AppData\Local\Temp\opencode`。
