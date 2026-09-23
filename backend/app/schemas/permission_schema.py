"""权限数据模型：角色可访问的知识库分类范围（功能权限 + 数据权限）。

阶段四「知识库权限配置」中的「可访问分类范围」落地于 sys_role_category 表。
空集合 = 不限制（可访问全部分类）。
"""

from pydantic import BaseModel, Field


class RoleCategoryGrantIn(BaseModel):
    category_ids: list[int] = Field(default_factory=list, description="可访问分类ID集合（空数组=不限制）")


class RoleCategoryOut(BaseModel):
    role_id: int
    category_ids: list[int] = Field(default_factory=list)
