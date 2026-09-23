"""模型提供商（sys_provider）入参 / 出参模型。"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProviderBase(BaseModel):
    name: str = Field(..., max_length=100, description="提供商名称")
    endpoint: str = Field(..., max_length=255, description="API调用地址")
    model: str = Field(..., max_length=100, description="模型名称")
    api_key: str = Field(default="", max_length=500, description="API密钥")


class ProviderCreate(ProviderBase):
    pass


class ProviderUpdate(BaseModel):
    name: str | None = Field(None, max_length=100)
    endpoint: str | None = Field(None, max_length=255)
    model: str | None = Field(None, max_length=100)
    api_key: str | None = Field(None, max_length=500)


class ProviderOut(ProviderBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    create_time: datetime
    update_time: datetime
