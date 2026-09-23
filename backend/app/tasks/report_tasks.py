"""报表异步任务：后台批量报表计算、数据汇总（阶段七实现明细，此处落地任务骨架）。"""

import logging

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.report_tasks.build_report", bind=True)
def build_report(self, report_id: int) -> dict:
    """报表批量计算（Phase 7 实现）"""
    logger.info("收到报表计算任务 report_id=%s", report_id)
    # TODO(Phase 7)：数据汇总 → 图表数据生成 → AI 解读 → 导出
    return {"report_id": report_id, "status": "pending"}