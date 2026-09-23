"""角色管理接口（sys_role）。

- GET    /api/v1/role           分页列表（可选 keyword 筛选）
- GET    /api/v1/role/all       全部角色（用户绑定下拉用，不分页）
- POST   /api/v1/role           新增
- PUT    /api/v1/role/{id}      修改
- DELETE /api/v1/role/{id}      删除（校验用户绑定）
鉴权：仅超级管理员。
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import require_super_admin
from app.config import constants
from app.core.database import get_db
from app.schemas.common import PageResult
from app.schemas.role_schema import RoleCreate, RoleOut, RoleUpdate
from app.services.role_service import RoleService

router = APIRouter(
    prefix="/role",
    tags=["角色管理"],
    dependencies=[Depends(require_super_admin)],
)

_service = RoleService()


@router.get("", response_model=PageResult[RoleOut])
def list_roles(
    pageNum: int = Query(constants.DEFAULT_PAGE_NUM, ge=1),
    pageSize: int = Query(constants.DEFAULT_PAGE_SIZE, ge=1, le=constants.MAX_PAGE_SIZE),
    keyword: str | None = Query(None),
    db: Session = Depends(get_db),
):
    return _service.list_roles(db, pageNum, pageSize, keyword)


@router.get("/all", response_model=list[RoleOut])
def all_roles(db: Session = Depends(get_db)):
    return _service.list_all(db)


@router.post("", response_model=RoleOut)
def create_role(payload: RoleCreate, db: Session = Depends(get_db)):
    return _service.create_role(db, payload)


@router.put("/{role_id}", response_model=RoleOut)
def update_role(role_id: int, payload: RoleUpdate, db: Session = Depends(get_db)):
    return _service.update_role(db, role_id, payload)


@router.delete("/{role_id}")
def delete_role(role_id: int, db: Session = Depends(get_db)):
    _service.delete_role(db, role_id)
    return {"message": "删除成功"}
