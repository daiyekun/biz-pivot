"""部门 / 公司（sys_department）仓储层。"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import constants
from app.models.sys import SysDepartment, SysUser


class DeptRepository:
    def list_all(self, db: Session) -> list[SysDepartment]:
        """整树加载（树形页面不分页）"""
        return list(
            db.scalars(
                select(SysDepartment)
                .where(SysDepartment.state != constants.STATE_DELETED)
                .order_by(SysDepartment.sort_order, SysDepartment.id)
            ).all()
        )

    def get(self, db: Session, dept_id: int) -> SysDepartment | None:
        return db.get(SysDepartment, dept_id)

    def create(self, db: Session, data: dict) -> SysDepartment:
        """新增：add + flush（仅回填自增 id，path/company_id 由业务层补齐后再提交）"""
        dept = SysDepartment(**data)
        db.add(dept)
        db.flush()
        return dept

    def commit(self, db: Session, dept: SysDepartment) -> SysDepartment:
        db.commit()
        db.refresh(dept)
        return dept

    def update(self, db: Session, dept: SysDepartment, data: dict) -> SysDepartment:
        for key, value in data.items():
            setattr(dept, key, value)
        db.commit()
        db.refresh(dept)
        return dept

    def soft_delete(self, db: Session, dept: SysDepartment) -> None:
        dept.state = constants.STATE_DELETED
        db.commit()

    def list_descendants(self, db: Session, path_prefix: str) -> list[SysDepartment]:
        """按物化路径前缀查全部子孙（含自身）"""
        return list(
            db.scalars(
                select(SysDepartment).where(
                    SysDepartment.path.like(f"{path_prefix}%"),
                    SysDepartment.state != constants.STATE_DELETED,
                )
            ).all()
        )

    def count_children(self, db: Session, pid: int) -> int:
        return db.scalar(
            select(func.count())
            .select_from(SysDepartment)
            .where(SysDepartment.pid == pid, SysDepartment.state != constants.STATE_DELETED)
        ) or 0

    def count_users(self, db: Session, dept_id: int) -> int:
        return db.scalar(
            select(func.count())
            .select_from(SysUser)
            .where(SysUser.dept_id == dept_id, SysUser.state != constants.STATE_DELETED)
        ) or 0
