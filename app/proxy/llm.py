"""LLM client abstraction.

The proxy depends on the ``LLMClient`` protocol, not on the OpenAI SDK directly.
Reason: it makes the hot path testable (tests inject a fake via FastAPI's
dependency override) and keeps the provider swappable. The OpenAI client is
created lazily on first use, so the block path and the test suite never need a
real API key.
"""

from __future__ import annotations

from typing import Protocol

from openai import AsyncOpenAI

from app.core.config import settings


class LLMClient(Protocol):
    async def complete(self, messages: list[dict[str, str]], model: str) -> str:
        ...


class OpenAIClient:
    def __init__(self) -> None:
        self._client: AsyncOpenAI | None = None

    def _ensure(self) -> AsyncOpenAI:
        if self._client is None:
            if not settings.openai_api_key:
                raise RuntimeError(
                    "OPENAI_API_KEY is not set. Copy .env.example to .env and fill it in."
                )
            self._client = AsyncOpenAI(
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url,
            )
        return self._client

    async def complete(self, messages: list[dict[str, str]], model: str) -> str:
        client = self._ensure()
        resp = await client.chat.completions.create(model=model, messages=messages)  # type: ignore[arg-type]
        return resp.choices[0].message.content or ""


_singleton: LLMClient | None = None


def get_llm_client() -> LLMClient:
    """FastAPI dependency. Cheap to call; does not create the SDK client until
    a completion is actually requested."""
    global _singleton
    if _singleton is None:
        _singleton = OpenAIClient()
    return _singleton
