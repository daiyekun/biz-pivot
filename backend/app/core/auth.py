"""认证模块：密码加密 + JWT Token 生成/校验、用户身份解析。

密码采用 stdlib PBKDF2-HMAC-SHA256（pwd + slot 加盐），无需额外依赖；
Token 使用 PyJWT，密钥与有效期来自 settings。
"""

import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from app.config.settings import settings
from app.core.exceptions import UnauthorizedError

PBKDF2_ITERATIONS = 100_000


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


def create_token(user_id: int, account: str, is_super: bool = False,
                 extra: dict[str, Any] | None = None) -> str:
    """签发 JWT Token（含用户身份，供无状态校验）"""
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "account": account,
        "is_super": is_super,
        "iat": _now(),
        "exp": _now() + timedelta(minutes=settings.token_expire_minutes),
        "iss": settings.app_name,
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.secret_key, algorithm=settings.token_algorithm)


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


def make_token_pair(user_id: int, account: str, is_super: bool = False,
                    extra: dict[str, Any] | None = None) -> dict[str, Any]:
    """生成（后续阶段用于返回 access_token / refresh_token，本期仅 access）"""
    return {"access_token": create_token(user_id, account, is_super, extra)}