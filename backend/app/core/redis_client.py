"""Redis 全局连接与缓存工具。

会话、权限白名单、热点文档元信息全部外置 Redis，保证服务无状态可分布式。
"""

import json
from functools import lru_cache
from typing import Any

import redis

from app.config.settings import settings


@lru_cache
def _get_pool() -> redis.ConnectionPool:
    return redis.ConnectionPool.from_url(
        settings.redis_url,
        decode_responses=True,
        max_connections=50,
    )


def get_redis() -> redis.Redis:
    return redis.Redis(connection_pool=_get_pool())


def ping() -> bool:
    """连通性检查"""
    try:
        return bool(get_redis().ping())
    except redis.RedisError:
        return False


# ---------- JSON 读写快捷方法 ----------

def set_json(key: str, value: Any, ex: int | None = None) -> bool:
    return get_redis().set(key, json.dumps(value, ensure_ascii=False), ex=ex)


def get_json(key: str) -> Any:
    raw = get_redis().get(key)
    if raw is None:
        return None
    return json.loads(raw)


def delete(*keys: str) -> int:
    return get_redis().delete(*keys)


def exists(key: str) -> bool:
    return bool(get_redis().exists(key))


def expire(key: str, seconds: int) -> None:
    get_redis().expire(key, seconds)