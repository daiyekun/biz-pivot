"""用户（sys_user）仓储层。"""

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.config import constants
from app.models.sys import SysUser, SysUserRole


class UserRepository:
    def get(self, db: Session, user_id: int) -> SysUser | None:
        return db.get(SysUser, user_id)

    def get_by_account(self, db: Session, account: str) -> SysUser | None:
        return db.scalar(
            select(SysUser).where(
                SysUser.account == account, SysUser.state != constants.STATE_DELETED
            )
        )

    def get_by_account_exclude(self, db: Session, account: str, exclude_id: int) -> SysUser | None:
        return db.scalar(
            select(SysUser).where(
                SysUser.account == account,
                SysUser.state != constants.STATE_DELETED,
                SysUser.id != exclude_id,
            )
        )

    def list_page(
        self,
        db: Session,
        offset: int,
        limit: int,
        account: str | None = None,
        dept_id: int | None = None,
    ) -> tuple[list[SysUser], int]:
        base = SysUser.state != constants.STATE_DELETED
        stmt = select(SysUser).where(base)
        count_stmt = select(func.count()).select_from(SysUser).where(base)

        if account:
            like = f"%{account}%"
            stmt = stmt.where(SysUser.account.like(like))
            count_stmt = count_stmt.where(SysUser.account.like(like))
        if dept_id:
            stmt = stmt.where(SysUser.dept_id == dept_id)
            count_stmt = count_stmt.where(SysUser.dept_id == dept_id)

        total = db.scalar(count_stmt) or 0
        records = list(db.scalars(stmt.order_by(SysUser.id).offset(offset).limit(limit)).all())
        return records, total

    def create(self, db: Session, data: dict, role_ids: list[int]) -> SysUser:
        user = SysUser(**data)
        db.add(user)
        db.flush()
        for role_id in role_ids:
            db.add(SysUserRole(user_id=user.id, role_id=role_id))
        db.commit()
        db.refresh(user)
        return user

    def update(self, db: Session, user: SysUser, data: dict) -> SysUser:
        for key, value in data.items():
            setattr(user, key, value)
        db.commit()
        db.refresh(user)
        return user

    def set_roles(self, db: Session, user_id: int, role_ids: list[int]) -> None:
        db.execute(delete(SysUserRole).where(SysUserRole.user_id == user_id))
        for role_id in role_ids:
            db.add(SysUserRole(user_id=user_id, role_id=role_id))
        db.commit()

    def soft_delete(self, db: Session, user: SysUser) -> None:
        user.state = constants.STATE_DELETED
        # 释放唯一账号（软删后允许重建同名账号，避免 uk_sys_user_account 冲突）
        user.account = self._free_account(user.account, user.id)
        db.execute(delete(SysUserRole).where(SysUserRole.user_id == user.id))
        db.commit()

    def _free_account(self, account: str, user_id: int) -> str:
        suffix = f"__del_{user_id}"
        keep = max(1, 50 - len(suffix))
        return (account[:keep] + suffix)[:50]
