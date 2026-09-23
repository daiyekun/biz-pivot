"""部门管理接口（sys_department）。

- GET    /api/v1/dept/tree      无限级树（不分页；后台只读元数据，任一后台菜单授权可读）
- POST   /api/v1/dept           新增（需 dept:manage）
- PUT    /api/v1/dept/{id}      修改（支持更换父级，需 dept:manage）
- DELETE /api/v1/dept/{id}      删除（校验下级/归属用户，需 dept:manage）
鉴权：树查询走 require_backend_access；写操作走 dept:manage 菜单权限（超管全量）。
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_backend_access, require_menu_permission
from app.config import constants
from app.core.database import get_db
from app.schemas.dept_schema import DeptCreate, DeptOut, DeptUpdate
from app.services.dept_service import DeptService

router = APIRouter(prefix="/dept", tags=["部门管理"])

_service = DeptService()


@router.get("/tree", response_model=list[DeptOut], dependencies=[Depends(require_backend_access)])
def get_tree(db: Session = Depends(get_db)):
    return _service.tree(db)


@router.post("", response_model=DeptOut, dependencies=[Depends(require_menu_permission(constants.MENU_CODE_DEPT))])
def create_dept(payload: DeptCreate, db: Session = Depends(get_db)):
    return _service.create_dept(db, payload)


@router.put("/{dept_id}", response_model=DeptOut, dependencies=[Depends(require_menu_permission(constants.MENU_CODE_DEPT))])
def update_dept(dept_id: int, payload: DeptUpdate, db: Session = Depends(get_db)):
    return _service.update_dept(db, dept_id, payload)


@router.delete("/{dept_id}", dependencies=[Depends(require_menu_permission(constants.MENU_CODE_DEPT))])
def delete_dept(dept_id: int, db: Session = Depends(get_db)):
    _service.delete_dept(db, dept_id)
    return {"message": "删除成功"}
