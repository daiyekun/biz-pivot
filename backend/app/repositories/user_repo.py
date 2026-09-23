"""用户（sys_user）仓储层。"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.sys import SysUser


class UserRepository:
    def get(self, db: Session, user_id: int) -> SysUser | None:
        return db.get(SysUser, user_id)

    def get_by_account(self, db: Session, account: str) -> SysUser | None:
        return db.scalar(select(SysUser).where(SysUser.account == account))
