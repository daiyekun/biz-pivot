"""模型提供商（sys_provider）业务服务层。"""

from sqlalchemy.orm import Session

from app.core.exceptions import BizError, DuplicateError, NotFoundError
from app.repositories.provider_repo import ProviderRepository
from app.schemas.provider_schema import ProviderCreate, ProviderUpdate


class ProviderService:
    def __init__(self) -> None:
        self._repo = ProviderRepository()

    def list_providers(self, db: Session):
        return self._repo.list(db)

    def get_provider(self, db: Session, provider_id: int):
        provider = self._repo.get(db, provider_id)
        if provider is None:
            raise NotFoundError("模型提供商不存在")
        return provider

    def create_provider(self, db: Session, payload: ProviderCreate):
        if self._repo.get_by_name(db, payload.name) is not None:
            raise DuplicateError("提供商名称已存在")
        return self._repo.create(db, payload.model_dump())

    def update_provider(self, db: Session, provider_id: int, payload: ProviderUpdate):
        provider = self._repo.get(db, provider_id)
        if provider is None:
            raise NotFoundError("模型提供商不存在")

        data = payload.model_dump(exclude_unset=True)
        if data.get("name") and data["name"] != provider.name:
            if self._repo.get_by_name(db, data["name"], exclude_id=provider_id) is not None:
                raise DuplicateError("提供商名称已存在")
        return self._repo.update(db, provider, data)

    def delete_provider(self, db: Session, provider_id: int) -> None:
        provider = self._repo.get(db, provider_id)
        if provider is None:
            raise NotFoundError("模型提供商不存在")
        if self._repo.count_chat_roles(db, provider_id) > 0:
            raise BizError("该提供商已关联聊天角色，请先解除关联后再删除")
        self._repo.delete(db, provider)
