# OpenRouter LLM client — singleton ChatOpenAI pointing at OpenRouter's API.
# Phase 2: synchronous JSON calls for structured outputs (Rex, Evaluator).

from __future__ import annotations

import os
from contextlib import contextmanager
from contextvars import ContextVar

from langchain_openai import ChatOpenAI
from pydantic import SecretStr

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

ALLOWED_MODELS = {
    "anthropic/claude-sonnet-4.6",
    "anthropic/claude-haiku-4.5",
    "openai/gpt-4.1",
    "deepseek/deepseek-v4-flash",
    "deepseek/deepseek-v4-pro",
    "meta-llama/llama-3.3-70b-instruct",
}

_default_llm: ChatOpenAI | None = None
_runtime_api_key: ContextVar[str] = ContextVar("openrouter_api_key", default="")
_runtime_models: ContextVar[dict[str, str]] = ContextVar("model_overrides", default={})


@contextmanager
def llm_runtime(openrouter_api_key: str = "", model_overrides: dict[str, str] | None = None):
    api_key_token = _runtime_api_key.set(openrouter_api_key.strip())
    models_token = _runtime_models.set(model_overrides or {})
    try:
        yield
    finally:
        _runtime_api_key.reset(api_key_token)
        _runtime_models.reset(models_token)


def model_for(agent: str, default: str) -> str:
    model = _runtime_models.get().get(agent) or default
    if model not in ALLOWED_MODELS:
        raise ValueError(f"Unsupported model override for {agent}")
    return model


def _require_api_key() -> str:
    runtime_key = _runtime_api_key.get()
    if runtime_key:
        return runtime_key
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY is not set.")
    return key


def get_llm(model: str) -> ChatOpenAI:
    """Returns a ChatOpenAI configured for OpenRouter. Cached per model."""
    runtime_key = _runtime_api_key.get()
    if runtime_key:
        return ChatOpenAI(
            model=model,
            api_key=SecretStr(runtime_key),
            base_url="https://openrouter.ai/api/v1",
            temperature=0.7,
        )

    global _default_llm
    if _default_llm is None or _default_llm.model_name != model:
        _default_llm = ChatOpenAI(
            model=model,
            api_key=SecretStr(_require_api_key()),
            base_url="https://openrouter.ai/api/v1",
            temperature=0.7,
        )
    return _default_llm
