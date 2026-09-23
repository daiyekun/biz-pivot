"""用户与鉴权（sys_user / auth）入参、出参模型。"""

from datetime import datetime

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    account: str = Field(..., min_length=1, max_length=50, description="登录账号")
    password: str = Field(..., min_length=1, max_length=100, description="登录密码")


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., description="刷新令牌")


class UserOut(BaseModel):
    """当前登录用户信息（登录 / 刷新 / 资料返回）"""

    id: int
    name: str
    account: str
    dept_id: int | None = None
    company_id: int = 0
    phone: str | None = None
    email: str | None = None
    state: int = 0
    is_super: bool = False
    role_ids: list[int] = Field(default_factory=list)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
    user: UserOut


# ---------- 用户后台管理（阶段三） ----------

class UserCreate(BaseModel):
    name: str = Field(..., max_length=50, description="显示名称")
    account: str = Field(..., min_length=1, max_length=50, description="登录账号（唯一）")
    password: str = Field(..., min_length=1, max_length=100, description="初始密码")
    dept_id: int = Field(..., description="归属部门ID（必填）")
    phone: str | None = Field(None, max_length=20)
    email: str | None = Field(None, max_length=100)
    role_ids: list[int] = Field(default_factory=list, description="绑定角色ID（多选）")


class UserUpdate(BaseModel):
    name: str | None = Field(None, max_length=50)
    dept_id: int | None = Field(None, description="归属部门ID")
    phone: str | None = Field(None, max_length=20)
    email: str | None = Field(None, max_length=100)
    role_ids: list[int] | None = Field(None, description="绑定角色ID（多选，传空数组清空）")


class ResetPasswordRequest(BaseModel):
    password: str = Field(..., min_length=1, max_length=100, description="新密码")


class SetStateRequest(BaseModel):
    state: int = Field(..., description="0=启用 1=禁用")


class UserPageItem(BaseModel):
    """用户列表行数据（含部门名 / 角色信息）"""

    id: int
    name: str
    account: str
    dept_id: int | None = None
    dept_name: str = ""
    company_id: int = 0
    phone: str | None = None
    email: str | None = None
    state: int = 0
    role_ids: list[int] = Field(default_factory=list)
    role_names: list[str] = Field(default_factory=list)
    is_super: bool = False
    create_time: datetime | None = None
