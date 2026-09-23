"""部门管理接口（sys_department）。

- GET    /api/v1/dept/tree      无限级树（不分页）
- POST   /api/v1/dept           新增
- PUT    /api/v1/dept/{id}      修改（支持更换父级）
- DELETE /api/v1/dept/{id}      删除（校验下级/归属用户）
鉴权：仅超级管理员。
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_super_admin
from app.core.database import get_db
from app.schemas.dept_schema import DeptCreate, DeptOut, DeptUpdate
from app.services.dept_service import DeptService

router = APIRouter(
    prefix="/dept",
    tags=["部门管理"],
    dependencies=[Depends(require_super_admin)],
)

_service = DeptService()


@router.get("/tree", response_model=list[DeptOut])
def get_tree(db: Session = Depends(get_db)):
    return _service.tree(db)


@router.post("", response_model=DeptOut)
def create_dept(payload: DeptCreate, db: Session = Depends(get_db)):
    return _service.create_dept(db, payload)


@router.put("/{dept_id}", response_model=DeptOut)
def update_dept(dept_id: int, payload: DeptUpdate, db: Session = Depends(get_db)):
    return _service.update_dept(db, dept_id, payload)


@router.delete("/{dept_id}")
def delete_dept(dept_id: int, db: Session = Depends(get_db)):
    _service.delete_dept(db, dept_id)
    return {"message": "删除成功"}
