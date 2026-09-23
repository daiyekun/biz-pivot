"""部门 / 公司（sys_department）入参、出参模型。

无限级树形：pid + path 物化路径；is_company 区分公司节点（根）与部门节点。
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DeptCreate(BaseModel):
    pid: int = Field(0, description="上级节点ID，0=顶级(公司)")
    name: str = Field(..., max_length=200, description="公司名或部门名")
    sort_order: int = Field(0, description="同级排序")


class DeptUpdate(BaseModel):
    pid: int | None = Field(None, description="上级节点ID（更换父级时传入）")
    name: str | None = Field(None, max_length=200)
    sort_order: int | None = Field(None)


class DeptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    pid: int
    name: str
    is_company: int
    company_id: int
    path: str
    sort_order: int
    state: int
    children: list[DeptOut] = Field(default_factory=list)
    create_time: datetime | None = None
    update_time: datetime | None = None
