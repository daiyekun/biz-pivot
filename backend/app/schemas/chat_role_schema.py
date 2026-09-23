"""智能聊天角色（sys_chat_role）入参 / 出参模型。"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ChatRoleBase(BaseModel):
    name: str = Field(..., max_length=100, description="角色名称")
    description: str | None = Field(None, max_length=200, description="角色描述")
    system_prompt: str | None = Field(None, max_length=4000, description="系统提示词")
    temperature: float = Field(0.7, description="模型温度，默认0.7")
    provider_id: int | None = Field(None, description="模型提供商ID")


class ChatRoleCreate(ChatRoleBase):
    pass


class ChatRoleUpdate(BaseModel):
    name: str | None = Field(None, max_length=100)
    description: str | None = Field(None, max_length=200)
    system_prompt: str | None = Field(None, max_length=4000)
    temperature: float | None = Field(None)
    provider_id: int | None = Field(None)


class ChatRoleOut(ChatRoleBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    create_time: datetime
    update_time: datetime
