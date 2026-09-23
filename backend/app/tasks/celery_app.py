"""Celery 实例初始化与队列配置。

- Broker: RabbitMQ（amqp://...）
- Result: Redis
- 任务自动发现 app.tasks.* 下的 @celery_app.task
"""

from celery import Celery

from app.config.settings import settings

celery_app = Celery(
    "biz_pivot",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks.rag_tasks", "app.tasks.report_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
    task_default_queue="default",
)

# 通用队列与业务队列
celery_app.conf.task_routes = {
    "app.tasks.rag_tasks.*": {"queue": "rag"},
    "app.tasks.report_tasks.*": {"queue": "report"},
}