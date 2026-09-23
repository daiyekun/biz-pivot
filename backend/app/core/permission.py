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


def build_user_context(user, role_ids: list[int]) -> UserContext:
    """根据 sys_user 行与角色列表构建上下文。

    基础版：dept_ids 仅含当前部门，物化路径展开（path -> 祖先链）在
    阶段三部门模块落地后补齐，此处预留接口。
    """
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


def _role_has_menu(role_ids: list[int], menu_code: str) -> bool:
    """从 Redis 角色菜单缓存读取判定；缓存缺失默认拒绝（接口层二次拦截兜底在阶段四完善）。"""
    for role_id in role_ids:
        key = constants.REDIS_KEY_ROLE_MENU.format(role_id=role_id)
        menus = redis_client.get_json(key)
        if isinstance(menus, list) and menu_code in menus:
            return True
    return False


def cache_role_menus(role_id: int, menu_codes: list[str]) -> None:
    redis_client.set_json(
        constants.REDIS_KEY_ROLE_MENU.format(role_id=role_id),
        menu_codes,
        ex=int(ROLE_MENU_TTL.total_seconds()),
    )


def clear_role_menus(role_id: int) -> None:
    redis_client.delete(constants.REDIS_KEY_ROLE_MENU.format(role_id=role_id))