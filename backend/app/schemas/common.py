"""通用分页响应模型。

对齐开发计划 6.2 / 6.3：pageNum/pageSize 入参，返回 records/total/pages。
"""

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PageResult(BaseModel, Generic[T]):
    """表格列表统一分页返回结构"""

    records: list[T] = Field(default_factory=list, description="当前页数据")
    total: int = Field(0, description="总条数")
    pages: int = Field(0, description="总页数")
