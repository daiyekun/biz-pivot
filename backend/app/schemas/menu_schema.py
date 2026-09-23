"""菜单（sys_menu）与角色授权入参、出参模型。

对齐开发计划 6.1：菜单授权接口 /api/v1/menu。
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class MenuOut(BaseModel):
    """菜单节点（树形，含 code 权限标识，供前端勾选/映射知识库权限）"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    parent_id: int
    name: str
    path: str
    code: str = ""
    icon: str | None = None
    sort_order: int = 0
    page_type: str | None = None
    state: int = 0
    children: list[MenuOut] = Field(default_factory=list)


class RoleMenuGrantIn(BaseModel):
    """保存角色菜单授权入参"""

    menu_ids: list[int] = Field(default_factory=list, description="授权菜单ID集合（可传空数组清空）")


class RoleMenuOut(BaseModel):
    """角色已授权菜单ID集合出参"""

    role_id: int
    menu_ids: list[int] = Field(default_factory=list)


class MenuMineOut(BaseModel):
    """当前登录用户可访问的菜单路由集合（前端动态菜单用）"""

    paths: list[str] = Field(default_factory=list)
