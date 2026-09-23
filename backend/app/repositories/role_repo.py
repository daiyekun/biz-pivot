"""角色（sys_role）仓储层。"""

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.config import constants
from app.models.sys import SysMenuFunction, SysRole, SysRoleCategory, SysUser, SysUserRole


class RoleRepository:
    def list_all(self, db: Session) -> list[SysRole]:
        return list(
            db.scalars(
                select(SysRole)
                .where(SysRole.state != constants.STATE_DELETED)
                .order_by(SysRole.id)
            ).all()
        )

    def list_page(
        self,
        db: Session,
        offset: int,
        limit: int,
        keyword: str | None = None,
    ) -> tuple[list[SysRole], int]:
        base = SysRole.state != constants.STATE_DELETED
        stmt = select(SysRole).where(base)
        count_stmt = select(func.count()).select_from(SysRole).where(base)
        if keyword:
            like = f"%{keyword}%"
            stmt = stmt.where(SysRole.name.like(like))
            count_stmt = count_stmt.where(SysRole.name.like(like))

        total = db.scalar(count_stmt) or 0
        records = list(db.scalars(stmt.order_by(SysRole.id).offset(offset).limit(limit)).all())
        return records, total

    def get(self, db: Session, role_id: int) -> SysRole | None:
        return db.get(SysRole, role_id)

    def get_by_name(self, db: Session, name: str, exclude_id: int | None = None) -> SysRole | None:
        stmt = select(SysRole).where(SysRole.name == name, SysRole.state != constants.STATE_DELETED)
        if exclude_id is not None:
            stmt = stmt.where(SysRole.id != exclude_id)
        return db.scalar(stmt)

    def create(self, db: Session, data: dict) -> SysRole:
        role = SysRole(**data)
        db.add(role)
        db.commit()
        db.refresh(role)
        return role

    def update(self, db: Session, role: SysRole, data: dict) -> SysRole:
        for key, value in data.items():
            setattr(role, key, value)
        db.commit()
        db.refresh(role)
        return role

    def soft_delete(self, db: Session, role: SysRole) -> None:
        role.state = constants.STATE_DELETED
        # 释放唯一名称（软删后允许重建同名角色，避免 uk_sys_role_name 冲突）
        role.name = self._free_name(role.name, role.id)
        # 清理角色授权关联（菜单授权 + 可访问分类范围）
        db.execute(delete(SysMenuFunction).where(SysMenuFunction.role_id == role.id))
        db.execute(delete(SysRoleCategory).where(SysRoleCategory.role_id == role.id))
        db.commit()

    def _free_name(self, name: str, role_id: int) -> str:
        suffix = f"__del_{role_id}"
        keep = max(1, 50 - len(suffix))
        return (name[:keep] + suffix)[:50]

    def count_users(self, db: Session, role_id: int) -> int:
        """已绑定该角色且未删除的用户数"""
        return db.scalar(
            select(func.count())
            .select_from(SysUserRole)
            .join(SysUser, SysUserRole.user_id == SysUser.id)
            .where(
                SysUserRole.role_id == role_id,
                SysUser.state != constants.STATE_DELETED,
            )
        ) or 0
