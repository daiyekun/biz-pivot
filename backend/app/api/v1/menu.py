"""菜单授权接口（sys_menu / sys_menu_function / sys_role_category）。

- GET /api/v1/menu/tree                        菜单权限树（整树不分页，需 permission:grant）
- GET /api/v1/menu/role/{role_id}              角色已授权菜单 ID 集合（需 permission:grant）
- PUT /api/v1/menu/role/{role_id}              保存角色菜单授权（需 permission:grant）
- GET /api/v1/menu/role/{role_id}/categories   角色可访问知识库分类范围（需 permission:grant）
- PUT /api/v1/menu/role/{role_id}/categories   保存角色可访问分类范围（需 permission:grant）
- GET /api/v1/menu/mine                        当前登录用户可访问菜单路由（全员）
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_current_user, require_menu_permission
from app.config import constants
from app.core.database import get_db
from app.schemas.menu_schema import MenuMineOut, MenuOut, RoleMenuGrantIn, RoleMenuOut
from app.schemas.permission_schema import RoleCategoryGrantIn, RoleCategoryOut
from app.services.menu_service import MenuService

router = APIRouter(prefix="/menu", tags=["菜单授权"])

_service = MenuService()

_grant = Depends(require_menu_permission(constants.MENU_CODE_PERMISSION))


@router.get("/tree", response_model=list[MenuOut], dependencies=[_grant])
def get_menu_tree(db: Session = Depends(get_db)):
    return _service.tree(db)


@router.get("/role/{role_id}", response_model=RoleMenuOut, dependencies=[_grant])
def get_role_menus(role_id: int, db: Session = Depends(get_db)):
    return _service.get_role_menus(db, role_id)


@router.put("/role/{role_id}", response_model=RoleMenuOut, dependencies=[_grant])
def save_role_menus(role_id: int, payload: RoleMenuGrantIn, db: Session = Depends(get_db)):
    return _service.save_role_menus(db, role_id, payload.menu_ids)


@router.get("/role/{role_id}/categories", response_model=RoleCategoryOut, dependencies=[_grant])
def get_role_categories(role_id: int, db: Session = Depends(get_db)):
    return _service.get_role_categories(db, role_id)


@router.put("/role/{role_id}/categories", response_model=RoleCategoryOut, dependencies=[_grant])
def save_role_categories(role_id: int, payload: RoleCategoryGrantIn, db: Session = Depends(get_db)):
    return _service.save_role_categories(db, role_id, payload.category_ids)


@router.get("/mine", response_model=MenuMineOut)
def my_menus(current: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return MenuMineOut(paths=_service.get_user_menu_paths(db, current.ctx))
