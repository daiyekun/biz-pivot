"""Celery Worker 启动入口。

用法（在 backend 目录下执行）：
    celery -A app.tasks.celery_app:celery_app worker -l info -P solo

或直接：
    python celery_worker.py
"""

from app.tasks.celery_app import celery_app

if __name__ == "__main__":
    # Windows 开发环境使用 solo 池避免 fork 问题；Linux 生产可去掉 -P
    celery_app.start(argv=["worker", "-l", "info", "-P", "solo", "-Q", "default,rag,report"])