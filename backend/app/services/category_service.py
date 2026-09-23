"""知识库分类（sys_knowledge_category）业务服务层。

阶段四仅提供分类树查询；分类 CRUD 于阶段六补齐。
"""

from sqlalchemy.orm import Session

from app.repositories.category_repo import CategoryRepository
from app.schemas.category_schema import CategoryOut


class CategoryService:
    def __init__(self) -> None:
        self._repo = CategoryRepository()

    def tree(self, db: Session) -> list[CategoryOut]:
        nodes = self._repo.list_all(db)
        by_pid: dict[int, list[CategoryOut]] = {}
        for n in nodes:
            by_pid.setdefault(n.pid, []).append(self._to_node(n, []))

        def build(pid: int) -> list[CategoryOut]:
            result: list[CategoryOut] = []
            for item in by_pid.get(pid, []):
                item.children = build(item.id)
                result.append(item)
            return result

        return build(0)

    def _to_node(self, category, children: list[CategoryOut]) -> CategoryOut:
        return CategoryOut(
            id=category.id,
            name=category.name,
            pid=category.pid,
            path=category.path,
            sort_order=category.sort_order,
            state=category.state,
            children=children,
            create_time=category.create_time,
            update_time=category.update_time,
        )
