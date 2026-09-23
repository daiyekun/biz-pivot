"""系统模块接口：健康检查、系统信息、模型配置读取。

阶段一交付：连通性自检（DB / Redis / Qdrant），供前端首页展示底座状态。
"""

import logging

import httpx
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import constants
from app.config.settings import settings
from app.core.database import get_db
from app.core import redis_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/system", tags=["系统"])


@router.get("/health")
def health(db: Session = Depends(get_db)) -> dict:
    """健康检查：应用 + 数据库 + Redis + Qdrant"""
    deps = {}

    deps["application"] = True

    try:
        db.execute(text("SELECT 1"))
        deps["database"] = True
    except Exception as exc:  # noqa: BLE001
        logger.error("数据库健康检查失败：%s", exc)
        deps["database"] = False

    deps["redis"] = redis_client.ping()

    try:
        resp = httpx.get(f"{settings.qdrant_url}/collections", timeout=2)
        deps["qdrant"] = resp.status_code == 200
    except Exception:  # noqa: BLE001
        deps["qdrant"] = False

    healthy = all(v is True for v in deps.values())
    return {
        "status": "ok" if healthy else "degraded",
        "services": deps,
        "version": settings.app_version,
    }


@router.get("/info")
def system_info() -> dict:
    """系统基础信息（前端侧栏标题等展示）"""
    return {
        "app_name": settings.app_name,
        "version": settings.app_version,
        "debug": settings.debug,
    }


@router.get("/constants")
def public_constants() -> dict:
    """前端可用的公共常量（分页选项、权限枚举等）"""
    return {
        "page_size_options": constants.PAGE_SIZE_OPTIONS,
        "max_page_size": constants.MAX_PAGE_SIZE,
        "access_types": constants.ACCESS_TYPE_NAMES,
    }