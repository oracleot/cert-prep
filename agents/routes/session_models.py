from __future__ import annotations

from typing import Literal

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
    # Phase 11 — review queue. ``mode`` switches between fresh concept
    # selection (default ``"new"``) and spaced-review. ``concept_id`` pins
    # the session to a specific concept when provided; otherwise
    # ``select_review_concept`` picks the top due concept.
    mode: Literal["new", "review"] = "new"
    concept_id: str | None = None


class SessionSubmitRequest(BaseModel):
    thread_id: str
    user_answer: str
    answer_intent: str = "attempt"
    # Phase 11 — option-based session submission. When the active challenge
    # is option-based, the client sends the learner's selected labels here so
    # the backend can run exact-match evaluation. Free-text challenges leave
    # this empty.
    selected_labels: list[str] = Field(default_factory=list)
    model_overrides: dict[str, str] = Field(default_factory=dict)
    openrouter_api_key: str = ""


class SessionNextRequest(BaseModel):
    thread_id: str
    model_overrides: dict[str, str] = Field(default_factory=dict)
    openrouter_api_key: str = ""


class SessionStateRequest(BaseModel):
    thread_id: str
