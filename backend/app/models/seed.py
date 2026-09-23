"""系统种子数据：内置超级管理员、系统菜单、默认模型提供商、系统聊天角色（幂等）。

对应 PRD 7.1 系统初始化流程：启动建表 → 创建超管 → 初始化菜单 → 初始化提供商/聊天角色。
"""

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import constants
from app.config.settings import settings
from app.core import auth as auth_core
from app.core import redis_client
from app.models.sys import SysChatRole, SysDepartment, SysMenu, SysProvider, SysUser

logger = logging.getLogger(__name__)


def _get_or_create_root_company(db: Session) -> SysDepartment:
    """确保存在一个根公司节点（公司是部门树的根级节点）"""
    root = db.scalar(
        select(SysDepartment)
        .where(SysDepartment.is_company == 1, SysDepartment.state == constants.STATE_NORMAL)
        .order_by(SysDepartment.id)
        .limit(1)
    )
    if root is not None:
        return root

    root = SysDepartment(
        pid=0,
        name="企业",
        is_company=1,
        company_id=0,
        path="/1/",
        sort_order=0,
        state=constants.STATE_NORMAL,
    )
    db.add(root)
    db.flush()
    root.company_id = root.id
    root.path = f"/{root.id}/"
    db.commit()
    db.refresh(root)
    logger.info("系统初始化：创建根公司节点 id=%s", root.id)
    return root


def seed_menus(db: Session) -> None:
    """系统启动自动生成后台管理菜单（幂等）"""
    created = 0
    for m in constants.MENU_SEEDS:
        exists = db.scalar(select(SysMenu).where(SysMenu.path == m["path"]))
        if exists is not None:
            continue
        db.add(
            SysMenu(
                parent_id=0,
                name=m["name"],
                path=m["path"],
                code=m.get("code", m["path"]),
                icon=m.get("icon"),
                sort_order=m["sort_order"],
                page_type=m.get("page_type"),
                state=0,
            )
        )
        created += 1
    if created:
        db.commit()
        logger.info("系统初始化：写入菜单 %s 条", created)


def seed_default_provider(db: Session) -> SysProvider | None:
    """按 .env 的 LLM 配置创建默认模型提供商（幂等，无 LLM 配置则跳过）。"""
    if not settings.llm_base_url:
        logger.info("未配置 LLM_BASE_URL，跳过默认模型提供商种子")
        return None

    exists = db.scalar(
        select(SysProvider).where(SysProvider.name == constants.DEFAULT_PROVIDER_NAME)
    )
    if exists is not None:
        return exists

    provider = SysProvider(
        name=constants.DEFAULT_PROVIDER_NAME,
        endpoint=settings.llm_base_url,
        model=settings.llm_model or "",
        api_key=settings.llm_api_key or "",
    )
    db.add(provider)
    db.commit()
    db.refresh(provider)
    logger.info("系统初始化：创建默认模型提供商 id=%s", provider.id)
    return provider


def seed_chat_roles(db: Session) -> None:
    """内置系统聊天角色（通用助手 / 意图识别 / 语义识别，幂等）。

    系统发起聊天（意图识别、语义识别等）时程序直接指定这些角色。
    """
    provider = seed_default_provider(db)
    created = 0
    for item in constants.CHAT_ROLE_SEEDS:
        exists = db.scalar(select(SysChatRole).where(SysChatRole.name == item["name"]))
        if exists is not None:
            continue
        db.add(
            SysChatRole(
                name=item["name"],
                description=item.get("description"),
                system_prompt=item.get("system_prompt"),
                temperature=item.get("temperature", constants.DEFAULT_TEMPERATURE),
                provider_id=provider.id if provider else None,
            )
        )
        created += 1
    if created:
        db.commit()
        logger.info("系统初始化：写入聊天角色 %s 条", created)


def seed_super_admin(db: Session) -> None:
    """内置超级管理员（唯一、不可删除、不可禁用）。已存在则跳过。"""
    account = settings.super_admin_account
    exists = db.scalar(select(SysUser).where(SysUser.account == account))
    if exists is not None:
        return

    company = _get_or_create_root_company(db)
    slot, pwd_hash = auth_core.make_password(settings.super_admin_password)
    admin = SysUser(
        name=settings.super_admin_name,
        account=account,
        pwd=pwd_hash,
        slot=slot,
        dept_id=company.id,
        company_id=company.id,
        state=constants.STATE_NORMAL,
    )
    db.add(admin)
    db.commit()
    logger.info("系统初始化：创建内置超级管理员 %s（密码已在配置中，请尽快修改）", account)


def init_db_and_seed() -> None:
    """一键初始化：建表 + 菜单 + 超管（阶段一交付的初始化能力）"""
    from app.core.database import init_db

    init_db()

    from app.core.database import SessionLocal

    with SessionLocal() as db:
        seed_menus(db)
        seed_super_admin(db)
        seed_chat_roles(db)

    # 清除可能残留的旧缓存
    for key in redis_client.get_redis().scan_iter("user:perm:*"):
        redis_client.delete(key)
    logger.info("数据库初始化与种子数据写入完成")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_db_and_seed()