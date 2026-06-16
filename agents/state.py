# AppState TypedDict for the LangGraph session graph.
# All nodes read from and write to this shared state.

from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict


class Challenge(TypedDict):
    domain: str
    topic: str
    topic_id: str
    task_statement_id: str
    task_statement: str
    difficulty: str
    services: list[str]
    source_ids: list[str]
    scenario: str
    question: str


class EvaluationResult(TypedDict):
    outcome: str  # "correct" | "incorrect"
    reasoning: str


class Citation(TypedDict):
    url: str
    title: str
    snippet_id: str


class Exchange(TypedDict):
    cycle: int
    domain: str
    topic: str
    challenge: Challenge
    user_answer: str
    outcome: str
    sage_response: str
    citations: list[Citation]


class Domain(TypedDict):
    name: str
    weight: int
    topics: list[Any]
    task_statements: list[dict[str, str]]
    study_order: int
    performance_score: float


class AppState(TypedDict):
    # Identity comes from the Phase 3 anonymous browser user; Clerk replaces it in Phase 4.
    user_id: str
    exam_id: str
    curriculum_id: str
    curriculum: list[Domain]

    # Current session context — set by coach_open, updated by rex nodes
    current_domain: str
    current_topic: str
    current_topic_id: str
    current_task_statement_id: str
    current_task_statement: str
    current_services: list[str]
    current_source_ids: list[str]
    rex_difficulty: str  # "easy" | "medium" | "hard"
    max_cycles: int
    # "pressure_drills" | "guided_explanations" | "mixed_review" (default)
    learning_style: str
    local_timezone: str

    # 1-indexed cycle counter, advanced by rex_rechallenge.
    cycle: int

    # Per-cycle working state — overwritten each cycle
    current_challenge: Challenge
    user_answer: str
    last_evaluation: EvaluationResult

    # 2.3 affordance: pre-seeded user answers so the graph runs end-to-end.
    # Removed in 2.6 when LangGraph interrupts wait for real user input.
    # pending_user_answers: list[str]

    # Accumulated per-session — appended by sage_respond after each cycle
    # Annotated with operator.add so each append is additive, not overwriting
    session_history: Annotated[list[Exchange], operator.add]

    # Written by coach_open when a Postgres session row is created (2.4)
    db_session_id: str


def initial_state(
    user_id: str,
    exam_id: str = "dva-c02",
    local_timezone: str = "UTC",
) -> dict[str, Any]:
    """Returns the initial state dict for a new session.

    `pending_user_answers` is removed in 2.6 as we now use LangGraph interrupts.
    """
    return {
        "user_id": user_id,
        "exam_id": exam_id,
        "curriculum_id": "",
        "curriculum": [],
        "current_domain": "",
        "current_topic": "",
        "current_topic_id": "",
        "current_task_statement_id": "",
        "current_task_statement": "",
        "current_services": [],
        "current_source_ids": [],
        "rex_difficulty": "medium",
        "max_cycles": 2,
        "learning_style": "",
        "local_timezone": local_timezone,
        "cycle": 0,
        "current_challenge": {},
        "user_answer": "",
        "last_evaluation": {},
        "session_history": [],
        "db_session_id": "",
    }
