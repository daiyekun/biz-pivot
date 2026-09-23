"""认证模块：密码加密 + JWT Token 生成/校验、用户身份解析。

密码采用 stdlib PBKDF2-HMAC-SHA256（pwd + slot 加盐），无需额外依赖；
Token 使用 PyJWT，密钥与有效期来自 settings。
"""

import hashlib
import hmac
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from app.config.settings import settings
from app.core import redis_client
from app.core.exceptions import UnauthorizedError

logger = logging.getLogger(__name__)

PBKDF2_ITERATIONS = 100_000

TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"

# Redis 会话 Key（数据库设计 4.3 节 + 会话外置 Redis，分布式无状态）
SESSION_KEY_TMPL = "auth:session:{uid}"


# ============ 密码加密（pwd + slot 加盐） ============

def generate_slot() -> str:
    """生成随机盐串（hex）"""
    return secrets.token_hex(16)


def hash_password(password: str, slot: str) -> str:
    """使用 PBKDF2 派生密码哈希值并返回 hex 字符串"""
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(slot),
        PBKDF2_ITERATIONS,
    )
    return digest.hex()


def verify_password(password: str, slot: str, pwd_hash: str) -> bool:
    """校验密码（恒定时间比较防时序攻击）"""
    expected = hash_password(password, slot)
    return hmac.compare_digest(expected, pwd_hash)


def make_password(password: str) -> tuple[str, str]:
    """返回 (slot, pwd_hash) 便于入库"""
    slot = generate_slot()
    return slot, hash_password(password, slot)


# ============ JWT Token ============

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _create_token(user_id: int, account: str, is_super: bool,
                  token_type: str, expire_minutes: int) -> str:
    """签发 JWT Token（含用户身份，供无状态校验）"""
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "account": account,
        "is_super": is_super,
        "type": token_type,
        "iat": _now(),
        "exp": _now() + timedelta(minutes=expire_minutes),
        "iss": settings.app_name,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.token_algorithm)


def create_access_token(user_id: int, account: str, is_super: bool = False) -> str:
    return _create_token(
        user_id, account, is_super,
        TOKEN_TYPE_ACCESS, settings.token_expire_minutes,
    )


def create_refresh_token(user_id: int, account: str, is_super: bool = False) -> str:
    return _create_token(
        user_id, account, is_super,
        TOKEN_TYPE_REFRESH, settings.refresh_token_expire_minutes,
    )


def decode_token(token: str) -> dict[str, Any]:
    """校验并解析 JWT Token，失败抛出 401"""
    try:
        return jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.token_algorithm],
            issuer=settings.app_name,
        )
    except jwt.ExpiredSignatureError:
        raise UnauthorizedError("登录已过期，请重新登录")
    except jwt.InvalidTokenError:
        raise UnauthorizedError("无效的登录凭证")


def decode_access_token(token: str) -> dict[str, Any]:
    """校验 access token 并强制其类型为 access，防止 refresh token 越权访问。"""
    payload = decode_token(token)
    if payload.get("type") != TOKEN_TYPE_ACCESS:
        raise UnauthorizedError("无效的登录凭证")
    return payload


def decode_refresh_token(token: str) -> dict[str, Any]:
    """校验 refresh token 并确认其类型，失败抛出 401"""
    payload = decode_token(token)
    if payload.get("type") != TOKEN_TYPE_REFRESH:
        raise UnauthorizedError("无效的刷新凭证")
    return payload


def make_token_pair(user_id: int, account: str, is_super: bool = False) -> dict[str, Any]:
    """签发 access_token + refresh_token（会话写入 Redis）"""
    return {
        "access_token": create_access_token(user_id, account, is_super),
        "refresh_token": create_refresh_token(user_id, account, is_super),
        "token_type": "Bearer",
        "expires_in": settings.token_expire_minutes * 60,
    }


# ============ Redis 会话管理（登录 / 登出 / 刷新） ============

def _session_key(user_id: int) -> str:
    return SESSION_KEY_TMPL.format(uid=user_id)


def save_session(user_id: int, refresh_token: str, account: str, is_super: bool) -> None:
    """登录 / 刷新成功后将会话写入 Redis（TTL = refresh token 有效期）"""
    redis_client.set_json(
        _session_key(user_id),
        {
            "refresh_token": refresh_token,
            "account": account,
            "is_super": is_super,
            "login_time": _now().isoformat(),
        },
        ex=settings.refresh_token_expire_minutes * 60,
    )


def get_session(user_id: int) -> dict[str, Any] | None:
    return redis_client.get_json(_session_key(user_id))


def clear_session(user_id: int) -> None:
    redis_client.delete(_session_key(user_id))


def session_exists(user_id: int) -> bool:
    """会话是否存在（用于登出失效校验；Redis 不可用时降级放行，避免全站锁死）"""
    try:
        return redis_client.exists(_session_key(user_id))
    except Exception as exc:  # noqa: BLE001
        logger.warning("Redis 会话校验失败（降级放行）：%s", exc)
        return True