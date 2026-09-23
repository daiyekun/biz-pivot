"""登录鉴权接口：登录 / 刷新 / 登出 / 当前用户资料。

- POST /api/v1/auth/login     超级管理员与员工统一登录入口
- POST /api/v1/auth/refresh   刷新 access_token（refresh token 轮换）
- POST /api/v1/auth/logout    登出（清除 Redis 会话）
- GET  /api/v1/auth/profile   当前登录用户资料
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_current_user
from app.core.database import get_db
from app.schemas.user_schema import LoginRequest, RefreshRequest, TokenResponse, UserOut
from app.services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["鉴权"])

_service = UserService()


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    return _service.login(db, payload)


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    return _service.refresh(db, payload)


@router.post("/logout")
def logout(current: CurrentUser = Depends(get_current_user)):
    _service.logout(current.user.id)
    return {"message": "退出成功"}


@router.get("/profile", response_model=UserOut)
def profile(current: CurrentUser = Depends(get_current_user)):
    return _service.profile(current.user)
