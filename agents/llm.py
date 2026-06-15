# OpenRouter LLM client — singleton ChatOpenAI pointing at OpenRouter's API.
# Phase 2: synchronous JSON calls for structured outputs (Rex, Evaluator).

from __future__ import annotations

import os

from langchain_openai import ChatOpenAI

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

_default_llm: ChatOpenAI | None = None


def _require_api_key() -> str:
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY is not set.")
    return key


def get_llm(model: str) -> ChatOpenAI:
    """Returns a ChatOpenAI configured for OpenRouter. Cached per model."""
    global _default_llm
    if _default_llm is None or _default_llm.model_name != model:
        _default_llm = ChatOpenAI(
            model=model,
            api_key=_require_api_key(),
            base_url="https://openrouter.ai/api/v1",
            temperature=0.7,
        )
    return _default_llm
