"""角色（sys_role）入参、出参模型。"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RoleCreate(BaseModel):
    name: str = Field(..., max_length=50, description="角色名称")
    desc: str | None = Field(None, max_length=500, description="角色描述")
    state: int = Field(0, description="0=启用 1=禁用")


class RoleUpdate(BaseModel):
    name: str | None = Field(None, max_length=50)
    desc: str | None = Field(None, max_length=500)
    state: int | None = Field(None, description="0=启用 1=禁用")


class RoleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    desc: str | None = None
    state: int
    create_time: datetime | None = None
    update_time: datetime | None = None
