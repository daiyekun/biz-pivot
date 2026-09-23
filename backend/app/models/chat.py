"""对话模块：会话表、消息表。

对应数据库设计 2.10 ~ 2.11。
"""

from sqlalchemy import BigInteger, ForeignKey, Index, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IdMixin, StateMixin, TimestampMixin


# ---------- 2.10 对话会话 ----------
class ChatSession(IdMixin, TimestampMixin, StateMixin, Base):
    __tablename__ = "chat_session"

    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("sys_user.id"), comment="所属用户")
    title: Mapped[str] = mapped_column(String(200), comment="会话标题")

    __table_args__ = (
        Index("idx_chat_session_user_time", "user_id", "update_time"),
    )


# ---------- 2.11 对话消息 ----------
class ChatMessage(IdMixin, Base):
    __tablename__ = "chat_message"

    session_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("chat_session.id"), comment="会话ID")
    role: Mapped[int] = mapped_column(SmallInteger, comment="0=用户 1=AI")
    content: Mapped[str] = mapped_column(Text, comment="消息内容")
    token_count: Mapped[int] = mapped_column(BigInteger, default=0, comment="token数（统计用）")

    __table_args__ = (
        Index("idx_chat_message_session_time", "session_id", "id"),
    )