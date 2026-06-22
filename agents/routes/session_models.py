from __future__ import annotations

from pydantic import BaseModel, Field


class SessionStartRequest(BaseModel):
    user_id: str
    exam_id: str | None = None
    timezone: str = "UTC"
    learning_style: str = ""
    max_cycles: int = 2
    focus_domain: str = ""
    model_overrides: dict[str, str] = Field(default_factory=dict)
    openrouter_api_key: str = ""


class SessionSubmitRequest(BaseModel):
    thread_id: str
    user_answer: str
    answer_intent: str = "attempt"
    model_overrides: dict[str, str] = Field(default_factory=dict)
    openrouter_api_key: str = ""


class SessionNextRequest(BaseModel):
    thread_id: str
    model_overrides: dict[str, str] = Field(default_factory=dict)
    openrouter_api_key: str = ""


class SessionStateRequest(BaseModel):
    thread_id: str
