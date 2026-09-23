"""模型提供商（sys_provider）仓储层。"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.sys import SysChatRole, SysProvider


class ProviderRepository:
    def list(self, db: Session) -> list[SysProvider]:
        return list(db.scalars(select(SysProvider).order_by(SysProvider.id)).all())

    def get(self, db: Session, provider_id: int) -> SysProvider | None:
        return db.get(SysProvider, provider_id)

    def get_by_name(self, db: Session, name: str, exclude_id: int | None = None) -> SysProvider | None:
        stmt = select(SysProvider).where(SysProvider.name == name)
        if exclude_id is not None:
            stmt = stmt.where(SysProvider.id != exclude_id)
        return db.scalar(stmt)

    def create(self, db: Session, data: dict) -> SysProvider:
        provider = SysProvider(**data)
        db.add(provider)
        db.commit()
        db.refresh(provider)
        return provider

    def update(self, db: Session, provider: SysProvider, data: dict) -> SysProvider:
        for key, value in data.items():
            setattr(provider, key, value)
        db.commit()
        db.refresh(provider)
        return provider

    def delete(self, db: Session, provider: SysProvider) -> None:
        db.delete(provider)
        db.commit()

    def count_chat_roles(self, db: Session, provider_id: int) -> int:
        return db.scalar(
            select(func.count()).select_from(SysChatRole).where(SysChatRole.provider_id == provider_id)
        ) or 0
