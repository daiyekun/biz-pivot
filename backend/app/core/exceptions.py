"""全局异常定义与统一捕获处理。

业务代码抛 AppError 及其子类，由 main.py 注册的全局处理器统一
返回 {code, message, data: null} 结构，保证接口错误格式一致。
"""

from typing import Any


class AppError(Exception):
    """业务异常基类"""

    code: int = 500
    http_status: int = 500
    message: str = "系统繁忙，请稍后再试"
    data: Any = None

    def __init__(self, message: str | None = None, code: int | None = None, data: Any = None):
        if message is not None:
            self.message = message
        if code is not None:
            self.code = code
        self.data = data
        super().__init__(self.message)

    def to_dict(self) -> dict:
        return {"code": self.code, "message": self.message, "data": self.data}


class BizError(AppError):
    """通用业务错误（HTTP 200，业务码非 0）"""

    code = 400
    http_status = 200


class ValidationError(AppError):
    """参数校验失败"""

    code = 422
    http_status = 422


class UnauthorizedError(AppError):
    """未登录 / Token 失效"""

    code = 401
    http_status = 401


class ForbiddenError(AppError):
    """已登录但无权限"""

    code = 403
    http_status = 403


class NotFoundError(AppError):
    """资源不存在"""

    code = 404
    http_status = 404


class DuplicateError(AppError):
    """数据已存在（重复上传 / 重复账号等）"""

    code = 409
    http_status = 409


class DependencyError(AppError):
    """外部依赖（Redis / PG / LLM / 向量库）异常"""

    code = 500
    http_status = 500


def parse_app_error(exc: AppError) -> dict:
    """将业务异常转换为统一响应体"""
    return {"code": exc.code, "message": exc.message, "data": exc.data}