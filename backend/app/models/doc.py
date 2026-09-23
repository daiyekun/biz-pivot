"""文档异步解析任务表。

对应数据库设计 2.12。
"""

from sqlalchemy import BigInteger, ForeignKey, Index, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IdMixin, TimestampMixin


class DocParseTask(IdMixin, TimestampMixin, Base):
    __tablename__ = "doc_parse_task"

    kb_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("knowledge_base.id"), comment="文档ID")
    task_type: Mapped[int] = mapped_column(SmallInteger, comment="1=解析切片 2=向量化")
    status: Mapped[int] = mapped_column(
        SmallInteger, default=0, comment="0=待执行 1=执行中 2=成功 3=失败"
    )
    retry_count: Mapped[int] = mapped_column(BigInteger, default=0, comment="重试次数")
    error_msg: Mapped[str | None] = mapped_column(String(1000), nullable=True, comment="错误信息")
    celery_task_id: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="Celery任务ID")

    __table_args__ = (
        Index("idx_doc_parse_task_kb", "kb_id"),
        Index("idx_doc_parse_task_status", "status"),
    )