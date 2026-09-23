"""全局配置中心：通过 load_dotenv 加载 .env，用 os.getenv 读取。

所有可配置项统一收敛到 backend/.env（模板见 backend/.env.example），
settings.py 不硬编码任何密钥/地址，只做类型转换与派生属性计算。
"""

import os
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv

# backend/ 目录（settings.py 位于 backend/app/config/）
BASE_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE)


def _get_str(key: str, default: str = "") -> str:
    return os.getenv(key, default)


def _get_int(key: str, default: int = 0) -> int:
    val = os.getenv(key)
    if val is None or val.strip() == "":
        return default
    try:
        return int(val)
    except ValueError:
        return default


def _get_float(key: str, default: float = 0.0) -> float:
    val = os.getenv(key)
    if val is None or val.strip() == "":
        return default
    try:
        return float(val)
    except ValueError:
        return default


def _get_bool(key: str, default: bool = False) -> bool:
    val = os.getenv(key)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


class Settings:
    """从环境变量读取全部配置（含派生属性）。"""

    def __init__(self) -> None:
        # ---------- 应用基础 ----------
        self.app_name = _get_str("APP_NAME", "商枢 BizPivot 企业智能AI平台")
        self.app_version = _get_str("APP_VERSION", "0.1.0")
        self.debug = _get_bool("DEBUG", False)
        self.allowed_origins = _get_str(
            "ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
        )
        self.auto_init_db = _get_bool("AUTO_INIT_DB", True)

        # ---------- 认证 / Token ----------
        self.secret_key = _get_str("SECRET_KEY", "biz-pivot-secret-key-change-me-2026")
        self.token_algorithm = _get_str("TOKEN_ALGORITHM", "HS256")
        self.token_expire_minutes = _get_int("TOKEN_EXPIRE_MINUTES", 720)

        # ---------- 内置超级管理员 ----------
        self.super_admin_account = _get_str("SUPER_ADMIN_ACCOUNT", "admin")
        self.super_admin_password = _get_str("SUPER_ADMIN_PASSWORD", "Admin@123")
        self.super_admin_name = _get_str("SUPER_ADMIN_NAME", "超级管理员")

        # ---------- PostgreSQL ----------
        self.pg_host = _get_str("PG_HOST", "localhost")
        self.pg_port = _get_int("PG_PORT", 5432)
        self.pg_user = _get_str("PG_USER")
        self.pg_password = _get_str("PG_PASSWORD")
        self.pg_database = _get_str("PG_DATABASE")
        self.pg_database_url = _get_str("PG_DATABASE_URL")  # 可选覆盖，默认自动拼接
        self.pg_pool_size = _get_int("PG_POOL_SIZE", 10)
        self.pg_max_overflow = _get_int("PG_MAX_OVERFLOW", 20)

        # ---------- Redis ----------
        self.redis_host = _get_str("REDIS_HOST", "localhost")
        self.redis_port = _get_int("REDIS_PORT", 6379)
        self.redis_password = _get_str("REDIS_PASSWORD")
        self.redis_db = _get_int("REDIS_DB", 0)
        self.redis_url = _get_str("REDIS_URL")

        # ---------- RabbitMQ / Celery ----------
        self.rabbitmq_host = _get_str("RABBITMQ_HOST", "localhost")
        self.rabbitmq_port = _get_int("RABBITMQ_PORT", 5672)
        self.rabbitmq_user = _get_str("RABBITMQ_USER")
        self.rabbitmq_password = _get_str("RABBITMQ_PASSWORD")
        self.rabbitmq_vhost = _get_str("RABBITMQ_VHOST", "/")
        self.celery_broker_url = _get_str("CELERY_BROKER_URL")
        self.celery_result_backend = _get_str("CELERY_RESULT_BACKEND")

        # ---------- Qdrant 向量库 ----------
        self.qdrant_host = _get_str("QDRANT_HOST", "localhost")
        self.qdrant_port = _get_int("QDRANT_PORT", 6333)
        self.qdrant_grpc_port = _get_int("QDRANT_GRPC_PORT", 6334)
        self.qdrant_url = _get_str("QDRANT_URL", "http://localhost:6333")
        self.qdrant_collection_name = _get_str("QDRANT_COLLECTION_NAME", "knowledge_chunks")

        # ---------- LLM 客户端（OpenAI 兼容协议） ----------
        self.llm_base_url = _get_str("LLM_BASE_URL")
        self.llm_api_key = _get_str("LLM_API_KEY", "EMPTY")
        self.llm_model = _get_str("LLM_MODEL")
        self.llm_timeout_seconds = _get_float("LLM_TIMEOUT_SECONDS", 120.0)
        self.llm_max_tokens = _get_int("LLM_MAX_TOKENS", 2048)

        # ---------- OpenTelemetry / Jaeger ----------
        self.otel_exporter_otlp_endpoint = _get_str("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
        self.otel_service_name = _get_str("OTEL_SERVICE_NAME", "biz-pivot-fastapi")
        self.otel_enabled = _get_bool("OTEL_ENABLED", False)

        # ---------- 文件存储（预留 MinIO） ----------
        self.upload_dir = _get_str("UPLOAD_DIR", str(BASE_DIR / "uploads"))
        self.max_upload_size_mb = _get_int("MAX_UPLOAD_SIZE_MB", 50)

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def sqlalchemy_url(self) -> str:
        """SQLAlchemy 连接串：优先使用 .env 的 DATABASE_URL，否则按 PG_* 组件拼接（自动转义特殊字符）。"""
        if self.pg_database_url:
            return self.pg_database_url
        return (
            "postgresql+psycopg2://"
            f"{quote_plus(self.pg_user)}:{quote_plus(self.pg_password)}"
            f"@{self.pg_host}:{self.pg_port}/{self.pg_database}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()