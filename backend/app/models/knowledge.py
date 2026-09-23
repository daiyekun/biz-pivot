"""知识库表：知识分类（树形）、文档主表（V1.1 精简）、权限明细表（核心）。

对应数据库设计 2.7 ~ 2.9。
V1.1：knowledge_base 不冗余权限字段，五级权限统一收敛到 knowledge_permission。
"""

from sqlalchemy import BigInteger, ForeignKey, Index, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IdMixin, StateMixin, TimestampMixin


# ---------- 2.7 知识分类（树形） ----------
class SysKnowledgeCategory(IdMixin, TimestampMixin, StateMixin, Base):
    __tablename__ = "sys_knowledge_category"

    name: Mapped[str] = mapped_column(String(50), comment="类别名称")
    pid: Mapped[int] = mapped_column(BigInteger, default=0, comment="上级分类ID")
    path: Mapped[str] = mapped_column(String(500), default="/", comment="物化路径，如 /1/2/")
    sort_order: Mapped[int] = mapped_column(BigInteger, default=0, comment="排序")

    __table_args__ = (
        Index("idx_sys_knowledge_cat_pid", "pid"),
        Index("idx_sys_knowledge_cat_path", "path"),
    )


# ---------- 2.8 知识库文档主表（V1.1 精简：仅 2 个索引） ----------
class KnowledgeBase(IdMixin, TimestampMixin, StateMixin, Base):
    __tablename__ = "knowledge_base"

    file_name: Mapped[str] = mapped_column(String(500), comment="知识库文件名称")
    md5: Mapped[str] = mapped_column(String(200), comment="文件摘要（唯一，防重复上传）")
    file_path: Mapped[str] = mapped_column(String(800), comment="文件路径（MinIO/本地）")
    file_size: Mapped[int] = mapped_column(BigInteger, default=0, comment="文件大小（字节）")
    category_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("sys_knowledge_category.id"), comment="归属分类（必填）"
    )
    description: Mapped[str] = mapped_column(String(1000), comment="知识库描述（必填）")
    create_user_id: Mapped[int] = mapped_column(BigInteger, comment="创建人")
    parse_status: Mapped[int] = mapped_column(
        SmallInteger, default=0, comment="0=待解析 1=解析中 2=成功 3=失败"
    )
    vector_status: Mapped[int] = mapped_column(SmallInteger, default=0, comment="0=未入库 1=已入库 2=失败")
    chunk_count: Mapped[int] = mapped_column(BigInteger, default=0, comment="切片数量")

    __table_args__ = (
        Index("uk_knowledge_base_md5", "md5", unique=True),
        Index("idx_knowledge_base_category", "category_id"),
    )


# ---------- 2.9 知识库权限明细表（V1.1 唯一权限表 · 核心） ----------
class KnowledgePermission(IdMixin, Base):
    """每行 = 文档 + 一个可访问主体（用户/部门/公司/部门及子部门/跨部门）。

    五级权限上传时全部展开为明细行，本表是权限判定的唯一数据来源。
    """

    __tablename__ = "knowledge_permission"

    kb_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("knowledge_base.id"), comment="文档ID")
    access_type: Mapped[int] = mapped_column(
        SmallInteger, comment="1=用户 2=部门 3=公司 4=部门及子部门 5=跨部门"
    )
    target_id: Mapped[int] = mapped_column(BigInteger, comment="用户ID/部门ID/公司ID")

    __table_args__ = (
        Index("uk_knowledge_permission_target", "kb_id", "access_type", "target_id", unique=True),
        Index("idx_knowledge_permission_target", "access_type", "target_id"),
    )