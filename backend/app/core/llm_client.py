"""统一 LLM 客户端（兼容 OpenAI / Ollama / 国产模型）。

通过 OpenAI 兼容的 Chat Completions 协议访问（/chat/completions），
支持流式（text/event-stream）与非流式两种方式，前端对话由 SSE 转发。
"""

import json
import logging
from functools import lru_cache
from typing import AsyncIterator, Any

import httpx

from app.config.settings import get_settings
from app.core.exceptions import DependencyError

logger = logging.getLogger(__name__)


class LLMClient:
    """OpenAI 兼容 Chat Completions 客户端"""

    def __init__(self, base_url: str | None = None, api_key: str | None = None,
                 model: str | None = None, timeout: float | None = None,
                 max_tokens: int | None = None):
        settings = get_settings()
        self.base_url = (base_url or settings.llm_base_url).rstrip("/")
        self.api_key = api_key or settings.llm_api_key
        self.model = model or settings.llm_model
        self.timeout = timeout or settings.llm_timeout_seconds
        self.max_tokens = max_tokens or settings.llm_max_tokens

    def _endpoint(self) -> str:
        # 兼容 base_url 含 /v1 与不含 /v1 两种情况
        return f"{self.base_url}/chat/completions"

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _build_body(self, messages: list[dict[str, str]], stream: bool,
                    temperature: float = 0.7) -> dict[str, Any]:
        return {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            "temperature": temperature,
            "max_tokens": self.max_tokens,
        }

    @staticmethod
    def _extract_content(raw: str) -> list[str]:
        """解析非流式响应，返回内容片段列表"""
        data = json.loads(raw)
        choices = data.get("choices") or []
        texts = []
        for c in choices:
            msg = c.get("message") or {}
            if msg.get("content"):
                texts.append(msg["content"])
        return texts

    @staticmethod
    def _parse_stream_line(line: str) -> str | None:
        """解析单行 SSE `data: ...`，返回本轮增量文本或 None（结束/心跳）"""
        if not line.startswith("data:"):
            return None
        payload = line[len("data:"):].strip()
        if payload == "[DONE]":
            return None
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            return None
        choices = data.get("choices") or []
        for c in choices:
            delta = c.get("delta") or {}
            if delta.get("content"):
                return delta["content"]
        return None

    async def generate(self, messages: list[dict[str, str]],
                       temperature: float = 0.7) -> str:
        """非流式生成，返回完整文本"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                self._endpoint(),
                headers=self._headers(),
                json=self._build_body(messages, stream=False, temperature=temperature),
            )
        if resp.status_code != 200:
            logger.error("LLM 调用失败：status=%s body=%s", resp.status_code, resp.text[:500])
            raise DependencyError("LLM 服务调用失败，请稍后再试")
        texts = self._extract_content(resp.text)
        return "".join(texts)

    async def stream(self, messages: list[dict[str, str]],
                     temperature: float = 0.7) -> AsyncIterator[str]:
        """流式生成，逐段产出增量文本（调用方负责 SSE 转发）"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "POST",
                self._endpoint(),
                headers=self._headers(),
                json=self._build_body(messages, stream=True, temperature=temperature),
            ) as resp:
                if resp.status_code != 200:
                    body = (await resp.aread()).decode("utf-8", "ignore")
                    logger.error("LLM 流式调用失败：status=%s body=%s", resp.status_code, body[:500])
                    raise DependencyError("LLM 服务调用失败，请稍后再试")
                async for line in resp.aiter_lines():
                    if not line.strip():
                        continue
                    delta = self._parse_stream_line(line)
                    if delta:
                        yield delta

    async def summarize(self, text: str) -> str:
        """文本摘要"""
        prompt = f"请对以下内容做简洁中文摘要：\n\n{text}"[:4000]
        return await self.generate([{"role": "user", "content": prompt}])


@lru_cache
def get_llm_client() -> LLMClient:
    settings = get_settings()
    return LLMClient(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
        model=settings.llm_model,
        timeout=settings.llm_timeout_seconds,
        max_tokens=settings.llm_max_tokens,
    )