# AppState TypedDict for the LangGraph session graph.
# All nodes read from and write to this shared state.

from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict


class Challenge(TypedDict):
    domain: str
    topic: str
    scenario: str
    question: str


class EvaluationResult(TypedDict):
    outcome: str  # "correct" | "incorrect"
    reasoning: str


class Exchange(TypedDict):
    cycle: int
    domain: str
    topic: str
    challenge: Challenge
    user_answer: str
    outcome: str
    sage_response: str


class AppState(TypedDict):
    # Identity (hardcoded "dev-user" in Phase 2; real Clerk ID in Phase 4)
    user_id: str
    exam_id: str

    # Current session context — set by coach_open, updated by rex nodes
    current_domain: str
    current_topic: str
    rex_difficulty: str  # "easy" | "medium" | "hard"
    max_cycles: int

    # Per-cycle working state — overwritten each cycle
    current_challenge: Challenge
    user_answer: str
    last_evaluation: EvaluationResult

    # Accumulated per-session — appended by sage_respond after each cycle
    # Annotated with operator.add so each append is additive, not overwriting
    session_history: Annotated[list[Exchange], operator.add]

    # Written by coach_open when a Postgres session row is created
    db_session_id: str


def initial_state(user_id: str = "dev-user") -> dict[str, Any]:
    """Returns the initial state dict for a new session."""
    return {
        "user_id": user_id,
        "exam_id": "dva-c02",
        "current_domain": "",
        "current_topic": "",
        "rex_difficulty": "medium",
        "max_cycles": 2,
        "current_challenge": {},
        "user_answer": "",
        "last_evaluation": {},
        "session_history": [],
        "db_session_id": "",
    }
