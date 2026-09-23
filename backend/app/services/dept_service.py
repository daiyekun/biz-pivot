"""部门 / 公司（sys_department）业务服务层。

无限级树形：pid + path 物化路径；修改支持更换父级（防循环嵌套）；
删除前校验下级部门 / 归属用户。
"""

from sqlalchemy.orm import Session

from app.config import constants
from app.core.exceptions import BizError, NotFoundError
from app.repositories.dept_repo import DeptRepository
from app.schemas.dept_schema import DeptCreate, DeptOut, DeptUpdate


class DeptService:
    def __init__(self) -> None:
        self._repo = DeptRepository()

    # ---------- 查询 ----------
    def tree(self, db: Session) -> list[DeptOut]:
        nodes = self._repo.list_all(db)
        by_pid: dict[int, list[DeptOut]] = {}
        for n in nodes:
            by_pid.setdefault(n.pid, []).append(self._to_node(n, []))

        def build(pid: int) -> list[DeptOut]:
            result: list[DeptOut] = []
            for item in by_pid.get(pid, []):
                item.children = build(item.id)
                result.append(item)
            return result

        return build(0)

    # ---------- 新增 ----------
    def create_dept(self, db: Session, payload: DeptCreate) -> DeptOut:
        parent = None
        if payload.pid:
            parent = self._repo.get(db, payload.pid)
            if parent is None or parent.state == constants.STATE_DELETED:
                raise NotFoundError("父级部门不存在")

        is_company = 1 if payload.pid == 0 else 0
        dept = self._repo.create(
            db,
            {
                "pid": payload.pid,
                "name": payload.name,
                "is_company": is_company,
                "company_id": 0,
                "path": "/",
                "sort_order": payload.sort_order,
                "state": constants.STATE_NORMAL,
            },
        )
        self._fill_path(dept, parent)
        self._repo.commit(db, dept)
        return self._to_node(dept, [])

    # ---------- 修改 ----------
    def update_dept(self, db: Session, dept_id: int, payload: DeptUpdate) -> DeptOut:
        dept = self._repo.get(db, dept_id)
        if dept is None or dept.state == constants.STATE_DELETED:
            raise NotFoundError("部门不存在")

        data = payload.model_dump(exclude_unset=True)
        new_pid = data.get("pid", dept.pid)
        if new_pid is None:
            new_pid = dept.pid
            data.pop("pid", None)

        if "pid" in data and new_pid != dept.pid:
            if new_pid == dept.id:
                raise BizError("不能将部门移动到自己下")
            parent = None
            if new_pid:
                parent = self._repo.get(db, new_pid)
                if parent is None or parent.state == constants.STATE_DELETED:
                    raise NotFoundError("父级部门不存在")
                if parent.path.startswith(dept.path):
                    raise BizError("不能将部门移动到其子部门下（防循环嵌套）")

            old_path = dept.path
            dept.pid = new_pid
            dept.is_company = 1 if new_pid == 0 else 0
            self._fill_path(dept, parent)
            # 同步重写整棵子树的物化路径与 company_id
            for child in self._repo.list_descendants(db, old_path):
                if child.id == dept.id:
                    continue
                child.path = dept.path + child.path[len(old_path):]
                child.company_id = dept.company_id
            data.pop("pid", None)
        elif "pid" in data:
            data.pop("pid", None)

        data.pop("path", None)
        data.pop("company_id", None)
        data.pop("is_company", None)
        if data:
            self._repo.update(db, dept, data)
        else:
            db.commit()
            db.refresh(dept)
        return self._to_node(dept, [])

    # ---------- 删除 ----------
    def delete_dept(self, db: Session, dept_id: int) -> None:
        dept = self._repo.get(db, dept_id)
        if dept is None or dept.state == constants.STATE_DELETED:
            raise NotFoundError("部门不存在")
        if self._repo.count_children(db, dept_id) > 0:
            raise BizError("存在下级部门，请先处理子部门后再删除")
        if self._repo.count_users(db, dept_id) > 0:
            raise BizError("该部门下存在归属用户，请先迁移用户后再删除")
        self._repo.soft_delete(db, dept)

    # ---------- 内部工具 ----------
    def _fill_path(self, dept, parent) -> None:
        """回填物化路径与 company_id（需 dept.id 已回填）。"""
        if parent is not None:
            dept.path = f"{parent.path}{dept.id}/"
            dept.company_id = parent.id if parent.is_company == 1 else parent.company_id
        else:
            dept.path = f"/{dept.id}/"
            dept.company_id = dept.id

    def _to_node(self, dept, children: list[DeptOut]) -> DeptOut:
        return DeptOut(
            id=dept.id,
            pid=dept.pid,
            name=dept.name,
            is_company=dept.is_company,
            company_id=dept.company_id,
            path=dept.path,
            sort_order=dept.sort_order,
            state=dept.state,
            children=children,
            create_time=dept.create_time,
            update_time=dept.update_time,
        )
