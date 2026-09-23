"""菜单（sys_menu）与角色授权业务服务层。

阶段四核心：系统菜单权限树 + 知识库权限双重授权，保存即时生效。
- 菜单树：整树加载（parent_id + 排序），不分页
- 角色授权：全量覆盖写入 sys_menu_function，同步刷新 role:menu:{role_id} 缓存
- 缓存预热：登录时一次性加载用户角色菜单进 Redis，供后端接口层二次拦截
"""

from sqlalchemy.orm import Session

from app.config import constants
from app.core import permission as perm
from app.core.exceptions import NotFoundError
from app.core.permission import UserContext
from app.repositories.category_repo import CategoryRepository
from app.repositories.menu_repo import MenuRepository
from app.repositories.role_repo import RoleRepository
from app.schemas.menu_schema import MenuOut, RoleMenuOut
from app.schemas.permission_schema import RoleCategoryOut


class MenuService:
    def __init__(self) -> None:
        self._repo = MenuRepository()
        self._role_repo = RoleRepository()
        self._category_repo = CategoryRepository()

    # ---------- 菜单树 ----------
    def tree(self, db: Session) -> list[MenuOut]:
        nodes = self._repo.list_all(db)
        by_pid: dict[int, list[MenuOut]] = {}
        for n in nodes:
            by_pid.setdefault(n.parent_id, []).append(self._to_node(n, []))

        def build(pid: int) -> list[MenuOut]:
            result: list[MenuOut] = []
            for item in by_pid.get(pid, []):
                item.children = build(item.id)
                result.append(item)
            return result

        return build(0)

    # ---------- 角色授权 ----------
    def get_role_menus(self, db: Session, role_id: int) -> RoleMenuOut:
        self._ensure_role(db, role_id)
        return RoleMenuOut(role_id=role_id, menu_ids=self._repo.get_role_menu_ids(db, role_id))

    def save_role_menus(self, db: Session, role_id: int, menu_ids: list[int]) -> RoleMenuOut:
        self._ensure_role(db, role_id)
        menu_ids = list(dict.fromkeys(menu_ids))  # 去重保序
        if menu_ids:
            valid_ids = {m.id for m in self._repo.list_by_ids(db, menu_ids)}
            invalid = [m for m in menu_ids if m not in valid_ids]
            if invalid:
                raise NotFoundError(f"菜单不存在（id={invalid}）")

        self._repo.replace_role_menus(db, role_id, menu_ids)
        # 授权变更即时刷新角色菜单缓存（后端接口层二次拦截依据）
        perm.cache_role_menus(role_id, self._repo.get_role_menu_codes(db, role_id))
        return RoleMenuOut(role_id=role_id, menu_ids=menu_ids)

    # ---------- 角色可访问知识库分类（阶段四知识库权限配置） ----------
    def get_role_categories(self, db: Session, role_id: int) -> RoleCategoryOut:
        self._ensure_role(db, role_id)
        return RoleCategoryOut(role_id=role_id, category_ids=self._repo.get_role_category_ids(db, role_id))

    def save_role_categories(self, db: Session, role_id: int, category_ids: list[int]) -> RoleCategoryOut:
        self._ensure_role(db, role_id)
        category_ids = list(dict.fromkeys(category_ids))  # 去重保序
        if category_ids:
            valid_ids = {c.id for c in self._category_repo.list_by_ids(db, category_ids)}
            invalid = [c for c in category_ids if c not in valid_ids]
            if invalid:
                raise NotFoundError(f"知识库分类不存在（id={invalid}）")

        self._repo.replace_role_categories(db, role_id, category_ids)
        return RoleCategoryOut(role_id=role_id, category_ids=category_ids)

    # ---------- 当前用户可访问菜单（前端动态菜单） ----------
    def get_user_menu_paths(self, db: Session, ctx: UserContext) -> list[str]:
        """超级管理员返回全部菜单路由；普通用户返回其角色授权菜单路由"""
        menus = self._repo.list_all(db)
        if ctx.is_super:
            return [m.path for m in menus]
        codes: set[str] = set()
        for role_id in ctx.role_ids:
            codes.update(self._repo.get_role_menu_codes(db, role_id))
        return [m.path for m in menus if m.code in codes]

    # ---------- 缓存预热 ----------
    def warm_role_menus(self, db: Session, role_ids: list[int]) -> None:
        """登录/鉴权时预热角色菜单缓存（缺失才查库，避免每次请求全量加载）"""
        for role_id in role_ids:
            if perm.get_role_menus(role_id) is None:
                perm.cache_role_menus(role_id, self._repo.get_role_menu_codes(db, role_id))

    # ---------- 内部工具 ----------
    def _ensure_role(self, db: Session, role_id: int) -> None:
        role = self._role_repo.get(db, role_id)
        if role is None or role.state == constants.STATE_DELETED:
            raise NotFoundError("角色不存在")

    def _to_node(self, menu, children: list[MenuOut]) -> MenuOut:
        return MenuOut(
            id=menu.id,
            parent_id=menu.parent_id,
            name=menu.name,
            path=menu.path,
            code=menu.code or "",
            icon=menu.icon,
            sort_order=menu.sort_order,
            page_type=menu.page_type,
            state=menu.state,
            children=children,
        )
