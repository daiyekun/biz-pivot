"""知识库分类（sys_knowledge_category）仓储层。

阶段四仅提供整树读取；分类 CRUD 于阶段六补齐。
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import constants
from app.models.knowledge import SysKnowledgeCategory


class CategoryRepository:
    def list_all(self, db: Session) -> list[SysKnowledgeCategory]:
        """整树加载（树形页面不分页）"""
        return list(
            db.scalars(
                select(SysKnowledgeCategory)
                .where(SysKnowledgeCategory.state != constants.STATE_DELETED)
                .order_by(SysKnowledgeCategory.sort_order, SysKnowledgeCategory.id)
            ).all()
        )

    def list_by_ids(self, db: Session, category_ids: list[int]) -> list[SysKnowledgeCategory]:
        if not category_ids:
            return []
        return list(
            db.scalars(
                select(SysKnowledgeCategory).where(
                    SysKnowledgeCategory.id.in_(category_ids),
                    SysKnowledgeCategory.state != constants.STATE_DELETED,
                )
            ).all()
        )
