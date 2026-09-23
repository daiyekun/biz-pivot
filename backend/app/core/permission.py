"""权限模块：RBAC 权限校验、菜单权限拦截、用户权限上下文。

阶段一先落地「用户权限上下文」的构建与缓存、超管判定、菜单/上传权限的
统一校验入口；角色授权写入逻辑在阶段三/四接通后自动生效。

权限上下文缓存：Redis `user:perm:{uid}`（数据库设计 3.2 节）
角色菜单缓存：Redis `role:menu:{role_id}`
"""

import logging
from dataclasses import dataclass, field
from datetime import timedelta

from app.config import constants
from app.config.settings import settings
from app.core import redis_client

logger = logging.getLogger(__name__)

USER_PERM_TTL = timedelta(hours=12)
ROLE_MENU_TTL = timedelta(hours=12)


@dataclass
class UserContext:
    """当前用户权限上下文（数据权限计算基础）"""

    user_id: int
    account: str
    dept_id: int | None = None
    company_id: int = 0
    dept_ids: list[int] = field(default_factory=list)
    role_ids: list[int] = field(default_factory=list)
    is_super: bool = False


def is_super_account(account: str) -> bool:
    return account == settings.super_admin_account


def build_user_context(user, role_ids: list[int], dept_path: str | None = None) -> UserContext:
    """根据 sys_user 行与角色列表构建上下文。

    dept_ids 由物化路径展开：`/1/3/5/` -> [5, 3, 1]（当前部门 + 全部祖先部门），
    用于知识库数据权限的「部门/部门及子部门」判定（数据库设计 3.2 节）。
    """
    dept_ids = [user.dept_id] if user.dept_id else []
    if dept_path:
        try:
            dept_ids = [int(x) for x in dept_path.strip("/").split("/") if x]
        except ValueError:
            dept_ids = [user.dept_id] if user.dept_id else []
    return UserContext(
        user_id=user.id,
        account=user.account,
        dept_id=user.dept_id,
        company_id=user.company_id or 0,
        dept_ids=dept_ids,
        role_ids=role_ids,
        is_super=is_super_account(user.account),
    )


def cache_user_context(ctx: UserContext) -> None:
    key = constants.REDIS_KEY_USER_PERM.format(uid=ctx.user_id)
    redis_client.set_json(key, ctx.__dict__, ex=int(USER_PERM_TTL.total_seconds()))


def get_user_context(user_id: int) -> UserContext | None:
    key = constants.REDIS_KEY_USER_PERM.format(uid=user_id)
    data = redis_client.get_json(key)
    if data is None:
        return None
    return UserContext(**data)


def clear_user_context(user_id: int) -> None:
    redis_client.delete(constants.REDIS_KEY_USER_PERM.format(uid=user_id))


def has_upload_permission(ctx: UserContext) -> bool:
    """是否拥有知识库上传/管理权限。

    规则（PRD 4.1）：默认所有普通角色无上传权限；仅超管或经角色授权
    【文档上传】权限的角色可用。阶段四角色授权落地后，此处按角色菜单白名单判定。
    """
    if ctx.is_super:
        return True
    return _role_has_menu(ctx.role_ids, constants.MENU_CODE_KNOWLEDGE)


def has_menu_permission(ctx: UserContext, menu_code: str) -> bool:
    """角色是否拥有指定菜单（功能权限）"""
    if ctx.is_super:
        return True
    return _role_has_menu(ctx.role_ids, menu_code)


def has_category_permission(ctx: UserContext) -> bool:
    """是否拥有知识库分类管理权限（PRD 4.1：仅授权角色 + 超管可用）"""
    if ctx.is_super:
        return True
    return _role_has_menu(ctx.role_ids, constants.MENU_CODE_CATEGORY)


# 全部后台管理菜单权限标识（用于「后台访问」粗粒度判定：任一授权即可）
BACKEND_MENU_CODES = (
    constants.MENU_CODE_DEPT,
    constants.MENU_CODE_USER,
    constants.MENU_CODE_ROLE,
    constants.MENU_CODE_PERMISSION,
    constants.MENU_CODE_CATEGORY,
    constants.MENU_CODE_KNOWLEDGE,
    constants.MENU_CODE_PROVIDER,
    constants.MENU_CODE_CHAT_ROLE,
)


def has_backend_access(ctx: UserContext) -> bool:
    """是否拥有任一后台管理菜单权限（部门树/角色列表等只读元数据接口复用）"""
    if ctx.is_super:
        return True
    return any(_role_has_menu(ctx.role_ids, code) for code in BACKEND_MENU_CODES)


def _role_has_menu(role_ids: list[int], menu_code: str) -> bool:
    """从 Redis 角色菜单缓存读取判定；缓存缺失默认拒绝。

    缓存由 get_current_user 鉴权链路预热（见 api/deps.py），授权变更时
    menu_service 即时刷新，保证后端接口层二次拦截实时生效。
    """
    for role_id in role_ids:
        menus = get_role_menus(role_id)
        if isinstance(menus, list) and menu_code in menus:
            return True
    return False


def get_role_menus(role_id: int) -> list[str] | None:
    """读取角色菜单缓存（codes），未命中返回 None（供预热判断）"""
    key = constants.REDIS_KEY_ROLE_MENU.format(role_id=role_id)
    menus = redis_client.get_json(key)
    return menus if isinstance(menus, list) else None


def cache_role_menus(role_id: int, menu_codes: list[str]) -> None:
    redis_client.set_json(
        constants.REDIS_KEY_ROLE_MENU.format(role_id=role_id),
        menu_codes,
        ex=int(ROLE_MENU_TTL.total_seconds()),
    )


def clear_role_menus(role_id: int) -> None:
    redis_client.delete(constants.REDIS_KEY_ROLE_MENU.format(role_id=role_id))