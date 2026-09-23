"""全局鉴权拦截中间件。

未登录访问所有接口一律拒绝（401），统一跳转登录；禁用 / 删除账号彻底失效。
- 白名单：登录、刷新、健康检查（及 CORS 预检 OPTIONS）
- 校验链：解析 Bearer Token → Redis 会话存在性 → 账号状态（禁用/删除）
"""

import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import constants
from app.core import auth as auth_core
from app.core.database import SessionLocal
from app.core.exceptions import UnauthorizedError
from app.models.sys import SysUser

logger = logging.getLogger(__name__)

PUBLIC_PATHS = {
    "/api/v1/auth/login",
    "/api/v1/auth/refresh",
    "/api/v1/system/health",
}


def _unauthorized(message: str) -> JSONResponse:
    return JSONResponse(
        status_code=401,
        content={"code": 401, "message": message, "data": None},
    )


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if (
            request.method == "OPTIONS"
            or path in PUBLIC_PATHS
            or not path.startswith("/api/v1")
        ):
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        token = auth_header[7:] if auth_header.startswith("Bearer ") else ""
        if not token:
            return _unauthorized("未登录或登录已失效")

        try:
            payload = auth_core.decode_access_token(token)
        except UnauthorizedError as exc:
            return _unauthorized(exc.message)

        user_id = int(payload["sub"])

        if not auth_core.session_exists(user_id):
            return _unauthorized("登录已失效，请重新登录")

        with SessionLocal() as db:
            user = db.get(SysUser, user_id)
            if user is None:
                return _unauthorized("用户不存在")
            if user.state == constants.STATE_DISABLED:
                return _unauthorized("账号已被禁用")
            if user.state == constants.STATE_DELETED:
                return _unauthorized("用户已被删除")

        return await call_next(request)
