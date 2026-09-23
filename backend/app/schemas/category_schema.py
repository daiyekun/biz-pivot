"""知识库分类（sys_knowledge_category）入参、出参模型。

阶段四仅落地分类树查询（角色授权「可访问分类范围」选择用）；
分类 CRUD 于阶段六补齐。
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    pid: int
    path: str
    sort_order: int
    state: int
    children: list[CategoryOut] = Field(default_factory=list)
    create_time: datetime | None = None
    update_time: datetime | None = None
