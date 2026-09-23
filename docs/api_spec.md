# 商枢 BizPivot 统一接口文档

> 本文档随功能迭代同步更新。当前已落地阶段一（系统/模型提供商/聊天角色）与阶段二（登录鉴权）。

## 1. 通用约定

- 统一前缀：`/api/v1`
- 除登录、刷新、健康检查外，所有接口需携带请求头 `Authorization: Bearer <access_token>`，未登录一律返回 `401`
- 业务错误统一返回结构：`{ "code": <int>, "message": <str>, "data": null }`
- `state` 状态位：0=启用/显示，1=禁用/不显示，3=删除（软删除）

### 1.1 鉴权拦截

系统启动注册全局鉴权中间件（`core/auth_middleware.py`），白名单外接口一律拦截：

| 路径 | 是否公开 |
| ---- | -------- |
| `/api/v1/auth/login` | 是 |
| `/api/v1/auth/refresh` | 是 |
| `/api/v1/system/health` | 是 |
| 其余全部 | 否（需登录） |

校验链：解析 Bearer Token → Redis 会话存在性 → 账号状态（禁用/删除）→ 放行。

---

## 2. 鉴权模块 `/api/v1/auth`

### 2.1 登录

- **接口**：`POST /api/v1/auth/login`
- **说明**：超级管理员与员工统一登录入口；密码 PBKDF2（pwd + slot 加盐）校验；会话写入 Redis
- **入参**：

```json
{ "account": "admin", "password": "Admin@123" }
```

- **出参**：

```json
{
  "access_token": "<jwt>",
  "refresh_token": "<jwt>",
  "token_type": "Bearer",
  "expires_in": 43200,
  "user": {
    "id": 1,
    "name": "超级管理员",
    "account": "admin",
    "dept_id": 1,
    "company_id": 1,
    "phone": null,
    "email": null,
    "state": 0,
    "is_super": true,
    "role_ids": []
  }
}
```

- **错误**：账号或密码错误 `401`；账号已被禁用 `401`

### 2.2 刷新 Token

- **接口**：`POST /api/v1/auth/refresh`
- **入参**：`{ "refresh_token": "<jwt>" }`
- **出参**：同登录出参（access_token 与 refresh_token 轮换更新）
- **错误**：登录已失效 `401`

### 2.3 登出

- **接口**：`POST /api/v1/auth/logout`
- **说明**：清除 Redis 会话，此后该 access_token 彻底失效
- **出参**：`{ "message": "退出成功" }`

### 2.4 当前用户资料

- **接口**：`GET /api/v1/auth/profile`
- **出参**：同登录出参中的 `user` 对象

---

## 3. 系统模块 `/api/v1/system`

| 接口 | 方法 | 说明 |
| ---- | ---- | ---- |
| `/system/health` | GET | 健康检查（应用/数据库/Redis/Qdrant），公开 |
| `/system/info` | GET | 系统基础信息（需登录） |
| `/system/constants` | GET | 公共常量（分页选项/权限枚举，需登录） |

---

## 4. 模型提供商 `/api/v1/provider`（阶段一）

| 接口 | 方法 | 说明 |
| ---- | ---- | ---- |
| `/provider/list` | GET | 提供商列表 |
| `/provider` | POST | 新增提供商 |
| `/provider/{id}` | PUT | 修改提供商 |
| `/provider/{id}` | DELETE | 删除提供商（校验聊天角色引用） |

> 鉴权：阶段二起受全局中间件保护（需登录）；角色级权限在阶段三/四授权闭环后追加。

---

## 5. 聊天角色 `/api/v1/chat-role`（阶段一）

| 接口 | 方法 | 说明 |
| ---- | ---- | ---- |
| `/chat-role/list` | GET | 聊天角色列表 |
| `/chat-role` | POST | 新增聊天角色 |
| `/chat-role/{id}` | PUT | 修改聊天角色 |
| `/chat-role/{id}` | DELETE | 删除聊天角色（校验会话引用） |

> 鉴权：同上，需登录。
