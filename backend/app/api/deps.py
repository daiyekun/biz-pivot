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
from app.models.sys import SysDepartment, SysUser

logger = logging.getLogger(__name__)

_bearer = HTTPBearer(auto_error=False)

# 延迟导入，避免模块加载期循环依赖
_menu_service = None


def _get_menu_service():
    global _menu_service
    if _menu_service is None:
        from app.services.menu_service import MenuService

        _menu_service = MenuService()
    return _menu_service


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
    dept_path = None
    if user.dept_id:
        dept = db.get(SysDepartment, user.dept_id)
        if dept is not None:
            dept_path = dept.path
    ctx = perm.build_user_context(user, role_ids, dept_path)
    perm.cache_user_context(ctx)
    # 预热角色菜单缓存（role:menu:{role_id}），供后端接口层功能权限二次拦截
    try:
        _get_menu_service().warm_role_menus(db, role_ids)
    except Exception as exc:  # noqa: BLE001  预热失败不阻断鉴权
        logger.warning("预热角色菜单缓存失败：%s", exc)
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


def require_menu_permission(menu_code: str):
    """通用菜单功能权限拦截器（阶段四：后台入口 / 知识库上传 / 分类管理）"""

    def checker(current: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if not perm.has_menu_permission(current.ctx, menu_code):
            raise ForbiddenError("您没有该功能权限，请联系超级管理员授权")
        return current

    return checker


def require_category_permission(current: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """仅授权角色可进行知识库分类管理（PRD 4.1）"""
    if not perm.has_category_permission(current.ctx):
        raise ForbiddenError("您没有知识库分类管理权限，请联系超级管理员授权")
    return current


def require_backend_access(current: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """任一后台管理菜单授权即可访问的只读元数据接口（部门树 / 角色列表等）"""
    if not perm.has_backend_access(current.ctx):
        raise ForbiddenError("您没有后台管理权限，请联系超级管理员授权")
    return current


def get_client_ip(request: Request) -> str:
    """客户端 IP（后续审计日志用）"""
    return request.client.host if request.client else ""