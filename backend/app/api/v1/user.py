"""用户管理接口（sys_user）。

- GET    /api/v1/user                    分页列表（按用户名/部门筛选）
- POST   /api/v1/user                    新增（归属部门必填、可绑定角色）
- PUT    /api/v1/user/{id}               修改
- DELETE /api/v1/user/{id}               删除（超管不可删）
- PUT    /api/v1/user/{id}/password      重置密码
- PUT    /api/v1/user/{id}/state         启用 / 禁用
鉴权：user:manage 菜单权限（超管全量）。
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import require_menu_permission
from app.config import constants
from app.core.database import get_db
from app.schemas.common import PageResult
from app.schemas.user_schema import (
    ResetPasswordRequest,
    SetStateRequest,
    UserCreate,
    UserOut,
    UserPageItem,
    UserUpdate,
)
from app.services.user_service import UserService

router = APIRouter(
    prefix="/user",
    tags=["用户管理"],
    dependencies=[Depends(require_menu_permission(constants.MENU_CODE_USER))],
)

_service = UserService()


@router.get("", response_model=PageResult[UserPageItem])
def list_users(
    pageNum: int = Query(constants.DEFAULT_PAGE_NUM, ge=1),
    pageSize: int = Query(constants.DEFAULT_PAGE_SIZE, ge=1, le=constants.MAX_PAGE_SIZE),
    account: str | None = Query(None, description="用户名筛选"),
    dept_id: int | None = Query(None, description="部门筛选"),
    db: Session = Depends(get_db),
):
    return _service.list_users(db, pageNum, pageSize, account, dept_id)


@router.post("", response_model=UserOut)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    return _service.create_user(db, payload)


@router.put("/{user_id}", response_model=UserOut)
def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db)):
    return _service.update_user(db, user_id, payload)


@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    _service.delete_user(db, user_id)
    return {"message": "删除成功"}


@router.put("/{user_id}/password")
def reset_password(user_id: int, payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    _service.reset_password(db, user_id, payload)
    return {"message": "密码重置成功"}


@router.put("/{user_id}/state")
def set_state(user_id: int, payload: SetStateRequest, db: Session = Depends(get_db)):
    _service.set_state(db, user_id, payload.state)
    return {"message": "操作成功"}
