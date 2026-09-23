"""智能聊天角色（sys_chat_role）仓储层。"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.chat import ChatSession
from app.models.sys import SysChatRole


class ChatRoleRepository:
    def list(self, db: Session) -> list[SysChatRole]:
        return list(db.scalars(select(SysChatRole).order_by(SysChatRole.id)).all())

    def get(self, db: Session, role_id: int) -> SysChatRole | None:
        return db.get(SysChatRole, role_id)

    def get_by_name(self, db: Session, name: str, exclude_id: int | None = None) -> SysChatRole | None:
        stmt = select(SysChatRole).where(SysChatRole.name == name)
        if exclude_id is not None:
            stmt = stmt.where(SysChatRole.id != exclude_id)
        return db.scalar(stmt)

    def create(self, db: Session, data: dict) -> SysChatRole:
        role = SysChatRole(**data)
        db.add(role)
        db.commit()
        db.refresh(role)
        return role

    def update(self, db: Session, role: SysChatRole, data: dict) -> SysChatRole:
        for key, value in data.items():
            setattr(role, key, value)
        db.commit()
        db.refresh(role)
        return role

    def delete(self, db: Session, role: SysChatRole) -> None:
        db.delete(role)
        db.commit()

    def count_sessions(self, db: Session, role_id: int) -> int:
        return db.scalar(
            select(func.count()).select_from(ChatSession).where(ChatSession.chat_role_id == role_id)
        ) or 0
