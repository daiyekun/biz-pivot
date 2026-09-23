"""ORM 基类与通用字段混入。

对齐《数据库设计文档 V1.1》通用约定：
- 主键 id BIGINT GENERATED ALWAYS AS IDENTITY
- 全表含 create_time / update_time（TIMESTAMP，默认 now()）
- state：0=启用/显示，1=禁用/不显示，3=删除（软删除）
"""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Identity, SmallInteger, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

__all__ = ["Base", "IdMixin", "TimestampMixin", "StateMixin"]


class IdMixin:
    """自增主键"""

    id: Mapped[int] = mapped_column(
        BigInteger, Identity(always=True), primary_key=True, comment="主键"
    )


class TimestampMixin:
    """创建/更新时间（应用层维护 update_time）"""

    create_time: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="创建时间"
    )
    update_time: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )


class StateMixin:
    """状态字段：0=启用/显示，1=禁用/不显示，3=删除"""

    state: Mapped[int] = mapped_column(
        SmallInteger, default=0, server_default="0", comment="状态"
    )