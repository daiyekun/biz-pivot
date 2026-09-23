"""SSE 流式消息统一封装（状态推送 + 文本流推送）。

协议约定：每条事件以 `event: <type>` + `data: <json>` + 空行分隔。
前端 sse.js 按 event 类型分别处理。
"""

import json
from collections.abc import AsyncIterator
from typing import Any


def sse_packet(event: str, data: Any) -> str:
    """构造单条 SSE 报文"""
    payload = json.dumps(data, ensure_ascii=False, default=str)
    return f"event: {event}\ndata: {payload}\n\n"


def text_event(index: int, delta: str) -> str:
    """文本增量事件"""
    return sse_packet("message", {"index": index, "delta": delta})


def done_event(reason: str = "stop") -> str:
    """对话结束事件"""
    return sse_packet("done", {"reason": reason})


def status_event(step: str, message: str, extra: Any = None) -> str:
    """状态事件（RAG 检索中 / 解析进度等）"""
    return sse_packet("status", {"step": step, "message": message, "extra": extra})


def error_event(code: int, message: str) -> str:
    """错误事件"""
    return sse_packet("error", {"code": code, "message": message})


async def stream_to_sse(
    deltas: AsyncIterator[str],
    status_step: str = "generating",
    status_message: str = "AI 生成中",
) -> AsyncIterator[str]:
    """将 LLM 增量文本流转为 SSE 报文流。"""
    yield status_event(status_step, status_message)
    index = 0
    async for delta in deltas:
        if not delta:
            continue
        yield text_event(index, delta)
        index += 1
    yield done_event()