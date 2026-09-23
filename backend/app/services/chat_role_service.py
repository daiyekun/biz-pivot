"""智能聊天角色（sys_chat_role）业务服务层。"""

from sqlalchemy.orm import Session

from app.core.exceptions import BizError, DuplicateError, NotFoundError
from app.repositories.chat_role_repo import ChatRoleRepository
from app.repositories.provider_repo import ProviderRepository
from app.schemas.chat_role_schema import ChatRoleCreate, ChatRoleUpdate


class ChatRoleService:
    def __init__(self) -> None:
        self._repo = ChatRoleRepository()
        self._provider_repo = ProviderRepository()

    def list_roles(self, db: Session):
        return self._repo.list(db)

    def get_role(self, db: Session, role_id: int):
        role = self._repo.get(db, role_id)
        if role is None:
            raise NotFoundError("聊天角色不存在")
        return role

    def create_role(self, db: Session, payload: ChatRoleCreate):
        if self._repo.get_by_name(db, payload.name) is not None:
            raise DuplicateError("角色名称已存在")
        self._validate_provider(db, payload.provider_id)
        return self._repo.create(db, payload.model_dump())

    def update_role(self, db: Session, role_id: int, payload: ChatRoleUpdate):
        role = self._repo.get(db, role_id)
        if role is None:
            raise NotFoundError("聊天角色不存在")

        data = payload.model_dump(exclude_unset=True)
        if data.get("name") and data["name"] != role.name:
            if self._repo.get_by_name(db, data["name"], exclude_id=role_id) is not None:
                raise DuplicateError("角色名称已存在")
        if "provider_id" in data:
            self._validate_provider(db, data["provider_id"])
        return self._repo.update(db, role, data)

    def delete_role(self, db: Session, role_id: int) -> None:
        role = self._repo.get(db, role_id)
        if role is None:
            raise NotFoundError("聊天角色不存在")
        if self._repo.count_sessions(db, role_id) > 0:
            raise BizError("该聊天角色已关联会话，无法删除")
        self._repo.delete(db, role)

    def _validate_provider(self, db: Session, provider_id: int | None) -> None:
        if provider_id is None:
            return
        if self._provider_repo.get(db, provider_id) is None:
            raise NotFoundError("关联的模型提供商不存在")
