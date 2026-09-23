"""Token 统计、上下文占用率、自动压缩/摘要。

- 优先使用 tiktoken 精确统计，失败时降级为启发式估算（中英文混合场景）
- 达到阈值自动对历史消息做 LLM 摘要压缩，控制上下文长度
"""

import logging
from typing import Any

from app.config.constants import (
    CONTEXT_MAX_TOKENS,
    CONTEXT_SUMMARY_TARGET_RATIO,
    CONTEXT_SUMMARY_THRESHOLD_RATIO,
)

logger = logging.getLogger(__name__)

_ENCODER = None


def _get_encoder():
    """惰性加载 tiktoken，失败返回 None 走启发式"""
    global _ENCODER
    if _ENCODER is not None:
        return _ENCODER or None
    try:
        import tiktoken

        _ENCODER = tiktoken.get_encoding("cl100k_base")
    except Exception as exc:  # noqa: BLE001 网络/安装异常不影响主流程
        logger.warning("tiktoken 初始化失败，降级为启发式估算：%s", exc)
        _ENCODER = False
    return _ENCODER or None


def _fallback_count(text: str) -> int:
    """启发式估算：中文字符按 1 token/字，其余按 4 字符/token"""
    cjk = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")
    other = len(text) - cjk
    return cjk + other // 4 + 1


def count_tokens(text: str) -> int:
    """统计文本 token 数"""
    if not text:
        return 0
    encoder = _get_encoder()
    if encoder:
        try:
            return len(encoder.encode(text))
        except Exception:  # noqa: BLE001
            pass
    return _fallback_count(text)


def count_messages_tokens(messages: list[dict[str, str]]) -> int:
    return sum(count_tokens(str(m.get("content", ""))) for m in messages)


def context_usage_ratio(token_count: int, max_tokens: int = CONTEXT_MAX_TOKENS) -> float:
    """上下文占用率（0~1）"""
    if max_tokens <= 0:
        return 0.0
    return round(token_count / max_tokens, 4)


def needs_compression(token_count: int, max_tokens: int = CONTEXT_MAX_TOKENS) -> bool:
    """是否达到自动压缩阈值"""
    return token_count >= max_tokens * CONTEXT_SUMMARY_THRESHOLD_RATIO


def build_summary_prompt(messages: list[dict[str, str]], target_tokens: int) -> str:
    """生成摘要压缩提示词"""
    packed = "\n".join(
        f"{m.get('role', 'user')}: {m.get('content', '')}" for m in messages if m.get("content")
    )
    return (
        "请将以下对话内容压缩为一段不超过 "
        f"{max(200, target_tokens // 4)} 字的简洁摘要，"
        "保留关键信息、用户意图与未解决问题，不要丢失重要上下文：\n\n"
        f"{packed}"[:4000]
    )


async def summarize_messages(
    messages: list[dict[str, str]],
    llm_generate,
    max_tokens: int = CONTEXT_MAX_TOKENS,
) -> str:
    """对超长上下文做 LLM 摘要压缩，返回摘要文本。

    llm_generate: CoreLLM 的 async generate(messages) 或任何可调用对象（便于测试）。
    """
    target = int(max_tokens * CONTEXT_SUMMARY_TARGET_RATIO)
    prompt = build_summary_prompt(messages, target)
    try:
        return await llm_generate([{"role": "user", "content": prompt}])
    except Exception as exc:  # noqa: BLE001
        logger.error("上下文摘要压缩失败：%s", exc)
        return f"[历史对话摘要生成失败] 本次会话共 {len(messages)} 条消息。"


def trim_context(
    messages: list[dict[str, str]],
    max_tokens: int = CONTEXT_MAX_TOKENS,
) -> list[dict[str, str]]:
    """在 max_tokens 内尽量保留尾部（最新）消息，丢弃绝对超限的历史"""
    budget = max_tokens
    kept: list[dict[str, str]] = []
    for m in reversed(messages):
        cost = count_tokens(str(m.get("content", "")))
        if budget - cost < 0 and kept:
            break
        budget -= cost
        kept.insert(0, m)
    return kept