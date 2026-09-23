"""菜单（sys_menu）与角色-菜单授权（sys_menu_function）仓储层。"""

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.config import constants
from app.models.sys import SysMenu, SysMenuFunction, SysRoleCategory


class MenuRepository:
    def list_all(self, db: Session) -> list[SysMenu]:
        """整树加载全部菜单（菜单树不分页）"""
        return list(
            db.scalars(
                select(SysMenu)
                .where(SysMenu.state != constants.STATE_DELETED)
                .order_by(SysMenu.sort_order, SysMenu.id)
            ).all()
        )

    def get(self, db: Session, menu_id: int) -> SysMenu | None:
        return db.get(SysMenu, menu_id)

    def list_by_ids(self, db: Session, menu_ids: list[int]) -> list[SysMenu]:
        if not menu_ids:
            return []
        return list(
            db.scalars(
                select(SysMenu).where(
                    SysMenu.id.in_(menu_ids),
                    SysMenu.state != constants.STATE_DELETED,
                )
            ).all()
        )

    def get_role_menu_ids(self, db: Session, role_id: int) -> list[int]:
        """角色已授权的菜单 ID 集合"""
        return list(
            db.scalars(
                select(SysMenuFunction.menu_id).where(SysMenuFunction.role_id == role_id)
            ).all()
        )

    def get_role_menu_codes(self, db: Session, role_id: int) -> list[str]:
        """角色已授权菜单的权限标识（code）集合，供 Redis 角色菜单缓存 / 后端拦截判定"""
        return list(
            db.scalars(
                select(SysMenu.code)
                .join(SysMenuFunction, SysMenuFunction.menu_id == SysMenu.id)
                .where(
                    SysMenuFunction.role_id == role_id,
                    SysMenu.state != constants.STATE_DELETED,
                )
            ).all()
        )

    def replace_role_menus(self, db: Session, role_id: int, menu_ids: list[int]) -> None:
        """全量覆盖角色菜单授权（先清后插，事务提交）"""
        db.execute(delete(SysMenuFunction).where(SysMenuFunction.role_id == role_id))
        for menu_id in menu_ids:
            db.add(SysMenuFunction(role_id=role_id, menu_id=menu_id))
        db.commit()

    # ---------- 角色可访问知识库分类（阶段四知识库权限配置） ----------
    def get_role_category_ids(self, db: Session, role_id: int) -> list[int]:
        return list(
            db.scalars(
                select(SysRoleCategory.category_id).where(SysRoleCategory.role_id == role_id)
            ).all()
        )

    def replace_role_categories(self, db: Session, role_id: int, category_ids: list[int]) -> None:
        """全量覆盖角色可访问分类范围（先清后插，事务提交）"""
        db.execute(delete(SysRoleCategory).where(SysRoleCategory.role_id == role_id))
        for category_id in category_ids:
            db.add(SysRoleCategory(role_id=role_id, category_id=category_id))
        db.commit()
