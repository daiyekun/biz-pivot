"""用户与鉴权业务层：登录、刷新、登出、资料查询。

登录流程（PRD 5.1）：
- 统一入口，账号 + 密码校验（pwd + slot 加盐）
- 禁用账号禁止登录，返回友好提示
- 生成 access_token + refresh_token，会话写入 Redis（分布式无状态）
"""

from sqlalchemy.orm import Session

from app.config import constants
from app.config.settings import settings
from app.core import auth as auth_core
from app.core.exceptions import UnauthorizedError
from app.models.sys import SysUser
from app.repositories.user_repo import UserRepository
from app.schemas.user_schema import LoginRequest, RefreshRequest, UserOut


def _is_super(user: SysUser) -> bool:
    return user.account == settings.super_admin_account


def _build_user_out(user: SysUser) -> UserOut:
    role_ids = [r.id for r in user.roles] if user.roles else []
    return UserOut(
        id=user.id,
        name=user.name,
        account=user.account,
        dept_id=user.dept_id,
        company_id=user.company_id or 0,
        phone=user.phone,
        email=user.email,
        state=user.state,
        is_super=_is_super(user),
        role_ids=role_ids,
    )


class UserService:
    def __init__(self) -> None:
        self._repo = UserRepository()

    def login(self, db: Session, payload: LoginRequest) -> dict:
        user = self._repo.get_by_account(db, payload.account)
        if user is None:
            raise UnauthorizedError("账号或密码错误")
        if user.state == constants.STATE_DISABLED:
            raise UnauthorizedError("账号已被禁用")
        if user.state == constants.STATE_DELETED:
            raise UnauthorizedError("账号不存在或已被删除")

        if not auth_core.verify_password(payload.password, user.slot, user.pwd):
            raise UnauthorizedError("账号或密码错误")

        is_super = _is_super(user)
        tokens = auth_core.make_token_pair(user.id, user.account, is_super)
        auth_core.save_session(user.id, tokens["refresh_token"], user.account, is_super)
        return {**tokens, "user": _build_user_out(user)}

    def refresh(self, db: Session, payload: RefreshRequest) -> dict:
        data = auth_core.decode_refresh_token(payload.refresh_token)
        user_id = int(data["sub"])

        session = auth_core.get_session(user_id)
        if session is None or session.get("refresh_token") != payload.refresh_token:
            raise UnauthorizedError("登录已失效，请重新登录")

        user = self._repo.get(db, user_id)
        if user is None:
            raise UnauthorizedError("用户不存在")
        if user.state == constants.STATE_DISABLED:
            raise UnauthorizedError("账号已被禁用")
        if user.state == constants.STATE_DELETED:
            raise UnauthorizedError("用户已被删除")

        is_super = _is_super(user)
        tokens = auth_core.make_token_pair(user.id, user.account, is_super)
        auth_core.save_session(user.id, tokens["refresh_token"], user.account, is_super)
        return {**tokens, "user": _build_user_out(user)}

    def logout(self, user_id: int) -> None:
        auth_core.clear_session(user_id)

    def profile(self, user: SysUser) -> UserOut:
        return _build_user_out(user)
