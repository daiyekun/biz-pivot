"""全局路由依赖：当前用户解析、权限上下文、超级管理员/上传权限拦截器。

- get_current_user：解析 Bearer Token → 加载用户 → 构建并缓存权限上下文
- 后续阶段（角色授权落地后）直接复用 require_* 依赖做接口层二次拦截
"""

import logging
from dataclasses import dataclass

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core import auth as auth_core
from app.core import permission as perm
from app.core.database import get_db
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.redis_client import get_redis  # noqa: F401  统一导出
from app.models.sys import SysUser

logger = logging.getLogger(__name__)

_bearer = HTTPBearer(auto_error=False)


@dataclass
class CurrentUser:
    """当前登录用户（含权限上下文）"""

    user: SysUser
    ctx: perm.UserContext


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> CurrentUser:
    """解析并校验登录用户，构建权限上下文（登录接口依赖此能力）"""
    if credentials is None or not credentials.credentials:
        raise UnauthorizedError("未登录或登录已失效")

    payload = auth_core.decode_access_token(credentials.credentials)
    user_id = payload.get("sub")
    if user_id is None:
        raise UnauthorizedError("无效的登录凭证")

    user = db.get(SysUser, int(user_id))
    if user is None:
        raise UnauthorizedError("用户不存在")
    if user.state == 1:
        raise UnauthorizedError("账号已被禁用")
    if user.state == 3:
        raise UnauthorizedError("用户已被删除")

    role_ids = [r.id for r in user.roles] if user.roles else []
    ctx = perm.build_user_context(user, role_ids)
    perm.cache_user_context(ctx)
    return CurrentUser(user=user, ctx=ctx)


def require_super_admin(current: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """超级管理员专属接口（后台管理/授权）"""
    if not current.ctx.is_super:
        raise ForbiddenError("仅超级管理员可执行该操作")
    return current


def require_upload_permission(current: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """仅授权角色可上传文档（PRD 4.1 强约束）"""
    if not perm.has_upload_permission(current.ctx):
        raise ForbiddenError("您没有知识库文档上传权限，请联系超级管理员授权")
    return current


def get_client_ip(request: Request) -> str:
    """客户端 IP（后续审计日志用）"""
    return request.client.host if request.client else ""