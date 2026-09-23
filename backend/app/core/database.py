"""数据库连接与会话管理（同步 SQLAlchemy + PostgreSQL）。

- 建库建表：init_db()
- 请求级会话：get_db() 供 FastAPI 依赖注入
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.config.settings import settings


class Base(DeclarativeBase):
    """ORM 模型基类"""


engine = create_engine(
    settings.sqlalchemy_url,
    pool_pre_ping=True,
    pool_size=settings.pg_pool_size,
    max_overflow=settings.pg_max_overflow,
    echo=settings.debug,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI 依赖：请求级数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """创建所有表结构（幂等），需先 import models 保证注册"""
    import app.models  # noqa: F401  确保模型全部注册
    Base.metadata.create_all(bind=engine)