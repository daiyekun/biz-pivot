"""用户与鉴权业务层：登录、刷新、登出、资料查询。

登录流程（PRD 5.1）：
- 统一入口，账号 + 密码校验（pwd + slot 加盐）
- 禁用账号禁止登录，返回友好提示
- 生成 access_token + refresh_token，会话写入 Redis（分布式无状态）
"""

from math import ceil

from sqlalchemy.orm import Session

from app.config import constants
from app.config.settings import settings
from app.core import auth as auth_core
from app.core import permission as perm
from app.core.exceptions import BizError, DuplicateError, NotFoundError, UnauthorizedError
from app.models.sys import SysUser
from app.repositories.dept_repo import DeptRepository
from app.repositories.role_repo import RoleRepository
from app.repositories.user_repo import UserRepository
from app.schemas.common import PageResult
from app.schemas.user_schema import (
    LoginRequest,
    RefreshRequest,
    ResetPasswordRequest,
    UserCreate,
    UserOut,
    UserPageItem,
    UserUpdate,
)


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
        self._dept_repo = DeptRepository()
        self._role_repo = RoleRepository()

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

    # ============ 用户后台管理（阶段三） ============

    def list_users(
        self,
        db: Session,
        page: int,
        size: int,
        account: str | None = None,
        dept_id: int | None = None,
    ) -> PageResult:
        offset = (page - 1) * size
        records, total = self._repo.list_page(db, offset, size, account, dept_id)
        dept_map = {d.id: d.name for d in self._dept_repo.list_all(db)}

        items: list[UserPageItem] = []
        for u in records:
            roles = u.roles or []
            items.append(
                UserPageItem(
                    id=u.id,
                    name=u.name,
                    account=u.account,
                    dept_id=u.dept_id,
                    dept_name=dept_map.get(u.dept_id, ""),
                    company_id=u.company_id or 0,
                    phone=u.phone,
                    email=u.email,
                    state=u.state,
                    role_ids=[r.id for r in roles],
                    role_names=[r.name for r in roles],
                    is_super=_is_super(u),
                    create_time=u.create_time,
                )
            )
        return PageResult(records=items, total=total, pages=ceil(total / size) if size else 0)

    def create_user(self, db: Session, payload: UserCreate) -> UserOut:
        if self._repo.get_by_account(db, payload.account) is not None:
            raise DuplicateError("登录账号已存在")
        dept = self._dept_repo.get(db, payload.dept_id)
        if dept is None or dept.state != constants.STATE_NORMAL:
            raise NotFoundError("归属部门不存在或已禁用")
        self._validate_roles(db, payload.role_ids)

        slot, pwd_hash = auth_core.make_password(payload.password)
        company_id = dept.id if dept.is_company == 1 else dept.company_id
        user = self._repo.create(
            db,
            {
                "name": payload.name,
                "account": payload.account,
                "pwd": pwd_hash,
                "slot": slot,
                "dept_id": payload.dept_id,
                "company_id": company_id,
                "phone": payload.phone,
                "email": payload.email,
                "state": constants.STATE_NORMAL,
            },
            payload.role_ids,
        )
        return _build_user_out(user)

    def update_user(self, db: Session, user_id: int, payload: UserUpdate) -> UserOut:
        user = self._repo.get(db, user_id)
        if user is None or user.state == constants.STATE_DELETED:
            raise NotFoundError("用户不存在")

        data = payload.model_dump(exclude_unset=True)
        role_ids = data.pop("role_ids", None)

        if "dept_id" in data and data["dept_id"] is not None:
            dept = self._dept_repo.get(db, data["dept_id"])
            if dept is None or dept.state != constants.STATE_NORMAL:
                raise NotFoundError("归属部门不存在或已禁用")
            data["company_id"] = dept.id if dept.is_company == 1 else dept.company_id

        if role_ids is not None:
            self._validate_roles(db, role_ids)
            self._repo.set_roles(db, user_id, role_ids)

        if data:
            self._repo.update(db, user, data)
        perm.clear_user_context(user_id)
        db.refresh(user)
        return _build_user_out(user)

    def delete_user(self, db: Session, user_id: int) -> None:
        user = self._repo.get(db, user_id)
        if user is None or user.state == constants.STATE_DELETED:
            raise NotFoundError("用户不存在")
        if _is_super(user):
            raise BizError("超级管理员不可删除")
        self._repo.soft_delete(db, user)
        auth_core.clear_session(user_id)
        perm.clear_user_context(user_id)

    def reset_password(self, db: Session, user_id: int, payload: ResetPasswordRequest) -> None:
        user = self._repo.get(db, user_id)
        if user is None or user.state == constants.STATE_DELETED:
            raise NotFoundError("用户不存在")
        slot, pwd_hash = auth_core.make_password(payload.password)
        self._repo.update(db, user, {"slot": slot, "pwd": pwd_hash})
        auth_core.clear_session(user_id)

    def set_state(self, db: Session, user_id: int, state: int) -> None:
        if state not in (constants.STATE_NORMAL, constants.STATE_DISABLED):
            raise BizError("状态值非法")
        user = self._repo.get(db, user_id)
        if user is None or user.state == constants.STATE_DELETED:
            raise NotFoundError("用户不存在")
        if _is_super(user) and state == constants.STATE_DISABLED:
            raise BizError("超级管理员不可禁用")
        self._repo.update(db, user, {"state": state})
        if state != constants.STATE_NORMAL:
            auth_core.clear_session(user_id)
        perm.clear_user_context(user_id)

    def _validate_roles(self, db: Session, role_ids: list[int]) -> None:
        for role_id in set(role_ids):
            role = self._role_repo.get(db, role_id)
            if role is None or role.state == constants.STATE_DELETED:
                raise NotFoundError(f"角色不存在（id={role_id}）")
