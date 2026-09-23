"""ORM 模型包：导入即注册全部模型到 Base.metadata。"""

from app.models.base import Base, IdMixin, StateMixin, TimestampMixin
from app.models.sys import (
    SysChatRole,
    SysDepartment,
    SysMenu,
    SysMenuFunction,
    SysProvider,
    SysRole,
    SysUser,
    SysUserRole,
)
from app.models.knowledge import (
    KnowledgeBase,
    KnowledgePermission,
    SysKnowledgeCategory,
)
from app.models.chat import ChatMessage, ChatSession
from app.models.doc import DocParseTask
from app.models import seed

__all__ = [
    "Base",
    "IdMixin",
    "StateMixin",
    "TimestampMixin",
    "SysDepartment",
    "SysRole",
    "SysUser",
    "SysUserRole",
    "SysMenu",
    "SysMenuFunction",
    "SysProvider",
    "SysChatRole",
    "SysKnowledgeCategory",
    "KnowledgeBase",
    "KnowledgePermission",
    "ChatSession",
    "ChatMessage",
    "DocParseTask",
    "seed",
]