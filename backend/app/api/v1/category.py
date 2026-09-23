"""知识库分类接口（sys_knowledge_category）。

- GET /api/v1/category/tree  无限级分类树（不分页；后台只读元数据，任一后台菜单授权可读）
分类 CRUD 于阶段六补齐。
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_backend_access
from app.core.database import get_db
from app.schemas.category_schema import CategoryOut
from app.services.category_service import CategoryService

router = APIRouter(prefix="/category", tags=["知识库分类"])

_service = CategoryService()


@router.get("/tree", response_model=list[CategoryOut], dependencies=[Depends(require_backend_access)])
def get_tree(db: Session = Depends(get_db)):
    return _service.tree(db)
