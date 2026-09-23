"""系统管理表：部门/公司、角色、用户、用户-角色、菜单、角色-菜单。

对应数据库设计 2.1 ~ 2.6。
"""

from sqlalchemy import BigInteger, ForeignKey, Index, SmallInteger, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IdMixin, StateMixin, TimestampMixin


# ---------- 2.1 部门 / 公司（树形） ----------
class SysDepartment(IdMixin, TimestampMixin, StateMixin, Base):
    __tablename__ = "sys_department"

    pid: Mapped[int] = mapped_column(BigInteger, default=0, comment="上级节点ID，0=顶级（公司）")
    name: Mapped[str] = mapped_column(String(200), comment="公司名或部门名")
    is_company: Mapped[int] = mapped_column(SmallInteger, default=0, comment="0=部门 1=公司")
    company_id: Mapped[int] = mapped_column(BigInteger, default=0, comment="所属公司ID（冗余）")
    path: Mapped[str] = mapped_column(String(500), default="/", comment="物化路径，如 /1/3/5/")
    sort_order: Mapped[int] = mapped_column(BigInteger, default=0, comment="同级排序")

    __table_args__ = (
        Index("uk_sys_department_path", "path", unique=True),
        Index("idx_sys_department_pid", "pid"),
        Index("idx_sys_department_company", "company_id"),
    )


# ---------- 2.2 角色 ----------
class SysRole(IdMixin, TimestampMixin, StateMixin, Base):
    __tablename__ = "sys_role"

    name: Mapped[str] = mapped_column(String(50), comment="角色名称")
    desc: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="角色描述")

    __table_args__ = (
        Index("uk_sys_role_name", "name", unique=True),
    )


# ---------- 2.3 用户 ----------
class SysUser(IdMixin, TimestampMixin, StateMixin, Base):
    __tablename__ = "sys_user"

    name: Mapped[str] = mapped_column(String(50), comment="显示名称")
    account: Mapped[str] = mapped_column(String(50), comment="登录账号（唯一）")
    pwd: Mapped[str] = mapped_column(String(100), comment="密码（加密存储）")
    slot: Mapped[str] = mapped_column(String(100), comment="加盐串")
    dept_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("sys_department.id"), comment="部门ID（必填）"
    )
    company_id: Mapped[int] = mapped_column(BigInteger, default=0, comment="所属公司ID（冗余）")
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True, comment="手机号（可选）")
    email: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="邮箱（可选）")

    roles: Mapped[list["SysRole"]] = relationship(
        secondary="sys_user_role", lazy="selectin"
    )

    __table_args__ = (
        Index("uk_sys_user_account", "account", unique=True),
        Index("idx_sys_user_dept", "dept_id"),
        Index("idx_sys_user_company", "company_id"),
    )


# ---------- 2.4 用户 - 角色关联 ----------
class SysUserRole(IdMixin, Base):
    __tablename__ = "sys_user_role"

    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("sys_user.id"), comment="用户ID")
    role_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("sys_role.id"), comment="角色ID")

    __table_args__ = (
        UniqueConstraint("user_id", "role_id", name="uk_sys_user_role_ur"),
        Index("idx_sys_user_role_role", "role_id"),
    )


# ---------- 2.5 菜单定义 ----------
class SysMenu(IdMixin, Base):
    __tablename__ = "sys_menu"

    parent_id: Mapped[int] = mapped_column(BigInteger, default=0, comment="父菜单ID，0=顶级")
    name: Mapped[str] = mapped_column(String(50), comment="菜单名称")
    path: Mapped[str] = mapped_column(String(100), comment="前端路由，如 /admin/user")
    code: Mapped[str] = mapped_column(String(50), default="", comment="菜单权限标识")
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="图标")
    sort_order: Mapped[int] = mapped_column(BigInteger, default=0, comment="排序")
    page_type: Mapped[str | None] = mapped_column(String(20), nullable=True, comment="tree=树形 list=分页列表")
    state: Mapped[int] = mapped_column(SmallInteger, default=0, comment="0=启用 1=禁用")

    __table_args__ = (
        Index("idx_sys_menu_parent", "parent_id"),
    )


# ---------- 2.6 角色 - 菜单权限 ----------
class SysMenuFunction(IdMixin, Base):
    __tablename__ = "sys_menu_function"

    role_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("sys_role.id"), comment="角色ID")
    menu_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("sys_menu.id"), comment="菜单ID")

    __table_args__ = (
        UniqueConstraint("role_id", "menu_id", name="uk_sys_menu_function_rm"),
        Index("idx_sys_menu_function_menu", "menu_id"),
    )