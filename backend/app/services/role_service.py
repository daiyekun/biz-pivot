"""角色（sys_role）业务服务层。"""

from math import ceil

from sqlalchemy.orm import Session

from app.config import constants
from app.core import permission as perm
from app.core.exceptions import BizError, DuplicateError, NotFoundError
from app.repositories.role_repo import RoleRepository
from app.schemas.common import PageResult
from app.schemas.role_schema import RoleCreate, RoleUpdate


class RoleService:
    def __init__(self) -> None:
        self._repo = RoleRepository()

    def list_roles(self, db: Session, page: int, size: int, keyword: str | None = None) -> PageResult:
        offset = (page - 1) * size
        records, total = self._repo.list_page(db, offset, size, keyword)
        return PageResult(records=records, total=total, pages=ceil(total / size) if size else 0)

    def list_all(self, db: Session):
        return self._repo.list_all(db)

    def create_role(self, db: Session, payload: RoleCreate):
        if self._repo.get_by_name(db, payload.name) is not None:
            raise DuplicateError("角色名称已存在")
        data = payload.model_dump()
        data.setdefault("state", constants.STATE_NORMAL)
        return self._repo.create(db, data)

    def update_role(self, db: Session, role_id: int, payload: RoleUpdate):
        role = self._repo.get(db, role_id)
        if role is None or role.state == constants.STATE_DELETED:
            raise NotFoundError("角色不存在")

        data = payload.model_dump(exclude_unset=True)
        if data.get("name") and data["name"] != role.name:
            if self._repo.get_by_name(db, data["name"], exclude_id=role_id) is not None:
                raise DuplicateError("角色名称已存在")
        return self._repo.update(db, role, data)

    def delete_role(self, db: Session, role_id: int) -> None:
        role = self._repo.get(db, role_id)
        if role is None or role.state == constants.STATE_DELETED:
            raise NotFoundError("角色不存在")
        if self._repo.count_users(db, role_id) > 0:
            raise BizError("该角色已绑定用户，请先解除用户绑定后再删除")
        self._repo.soft_delete(db, role)
        perm.clear_role_menus(role_id)
