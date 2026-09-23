"""轻量数据库迁移：补齐 create_all 无法处理的存量表结构变更。

本项目未引入 Alembic，`Base.metadata.create_all()` 只会新建缺失的表、不会给
已存在的表增删列。V1.1/V1.2 的增量字段通过本模块在启动时幂等补齐。
"""

import logging

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

# 每条迁移：table=目标表, check_column=判断是否已迁移的列, ddl=按序执行的 DDL 语句
MIGRATIONS: list[dict] = [
    {
        # V1.2：chat_session 新增 chat_role_id（会话强制关联聊天角色）
        "table": "chat_session",
        "check_column": "chat_role_id",
        "ddl": [
            "ALTER TABLE chat_session ADD COLUMN IF NOT EXISTS chat_role_id BIGINT",
            "ALTER TABLE chat_session "
            "ADD CONSTRAINT fk_chat_session_role "
            "FOREIGN KEY (chat_role_id) REFERENCES sys_chat_role(id)",
            "CREATE INDEX IF NOT EXISTS idx_chat_session_role "
            "ON chat_session (chat_role_id)",
        ],
    },
]


def run_migrations(engine: Engine) -> None:
    """在 create_all 之后执行，幂等补齐缺失的列/约束/索引。"""
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    for migration in MIGRATIONS:
        table = migration["table"]
        if table not in existing_tables:
            continue
        columns = {c["name"] for c in inspector.get_columns(table)}
        if migration["check_column"] in columns:
            continue
        with engine.begin() as conn:
            for ddl in migration["ddl"]:
                try:
                    conn.execute(text(ddl))
                except Exception:  # noqa: BLE001  约束已存在等场景直接跳过
                    logger.warning("迁移语句执行跳过：%s", ddl)
                    continue
                logger.info("迁移执行：%s", ddl)
