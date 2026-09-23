"""RAG 异步任务：文档解析/切片/向量化（阶段六实现具体逻辑，此处落地任务骨架与健康任务）。

任务可追踪：doc_parse_task 状态落表 + celery_task_id 关联。
"""

import logging

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.rag_tasks.health_check", bind=True)
def health_check(self) -> dict:
    """Celery 健康检查任务（阶段一验证 worker 连通）"""
    return {"status": "ok", "worker": self.request.hostname or "", "task_id": self.request.id}


@celery_app.task(name="app.tasks.rag_tasks.parse_document", bind=True, max_retries=3)
def parse_document(self, task_id: int, kb_id: int) -> dict:
    """文档异步解析、切片、向量化入库（Phase 6 实现）"""
    logger.info("收到文档解析任务 task_id=%s kb_id=%s", task_id, kb_id)
    # TODO(Phase 6)：读取文件 → 切片 → 向量化 → 更新 parse/vector 状态与权限缓存
    return {"task_id": task_id, "kb_id": kb_id, "status": "pending"}