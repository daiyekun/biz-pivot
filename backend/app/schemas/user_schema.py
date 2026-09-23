"""用户与鉴权（sys_user / auth）入参、出参模型。"""

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
