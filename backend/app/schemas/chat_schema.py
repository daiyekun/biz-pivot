"""对话模块（chat_session / chat_message）入参 / 出参模型。

对齐补充需求：每个会话必须关联一个聊天角色（chat_role_id 必填）；
消息角色为枚举（0=系统 1=用户 2=助手 3=工具）。
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SessionCreate(BaseModel):
    title: str = Field("新会话", max_length=200, description="会话标题")
    chat_role_id: int = Field(..., description="聊天角色ID（必填，先选角色才能建会话）")


class SessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    chat_role_id: int
    title: str
    state: int
    create_time: datetime
    update_time: datetime


class MessageCreate(BaseModel):
    role: int = Field(..., description="消息角色：0=系统 1=用户 2=助手 3=工具")
    content: str = Field(..., description="消息内容")
    token_count: int = Field(0, description="token数")


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    role: int
    content: str
    token_count: int
    create_time: datetime
