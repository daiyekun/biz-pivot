"""商枢 BizPivot 后端应用入口。

- 应用生命周期：初始化链路追踪 → 自动建表 + 种子数据（超管/菜单）
- CORS：允许前端跨域
- 全局异常统一捕获（AppError → {code,message,data}）
- 路由：/api/v1/*
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.system import router as system_router
from app.api.v1.provider import router as provider_router
from app.api.v1.chat_role import router as chat_role_router
from app.config.settings import settings
from app.core.exceptions import AppError
from app.core.tracing import init_tracing

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_tracing()
    if settings.auto_init_db:
        try:
            from app.models.seed import init_db_and_seed

            init_db_and_seed()
        except Exception as exc:  # noqa: BLE001  数据库未就绪时不阻塞启动
            logger.error("自动初始化数据库失败：%s（请确认 PostgreSQL 已启动，或执行 python -m app.scripts.init_db）", exc)
    logger.info("%s %s 启动完成", settings.app_name, settings.app_version)
    yield
    logger.info("应用关闭")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="企业私有智能AI平台：AI闲聊 / RAG知识库 / 智能报表 / 企业RBAC权限体系",
    lifespan=lifespan,
)

# ---------- CORS ----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- 全局异常处理 ----------

@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    logger.warning("业务异常：[%s] %s（path=%s）", exc.code, exc.message, request.url.path)
    return JSONResponse(
        status_code=exc.http_status,
        content=exc.to_dict(),
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("未捕获异常（path=%s）", request.url.path)
    return JSONResponse(
        status_code=500,
        content={"code": 500, "message": "系统繁忙，请稍后再试", "data": None},
    )


# ---------- 路由注册 ----------

app.include_router(system_router, prefix="/api/v1")
app.include_router(provider_router, prefix="/api/v1")
app.include_router(chat_role_router, prefix="/api/v1")

# 后续阶段按模块增量挂载（auth/chat/rag/report/dept/user/role/menu/category）


@app.get("/", tags=["根"])
def root() -> dict:
    return {"name": settings.app_name, "version": settings.app_version, "docs": "/docs"}