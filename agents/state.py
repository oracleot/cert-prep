# AppState TypedDict for the LangGraph session graph.
# All nodes read from and write to this shared state.

from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict

from option_types import OptionLabel, ResponseMode


class Challenge(TypedDict):
    concept_id: str
    domain: str
    topic: str
    topic_id: str
    task_statement_id: str
    task_statement: str
    difficulty: str
    services: list[str]
    source_ids: list[str]
    familiarity_level: str
    scenario: str
    question: str
    # Phase 9.4 / 9.5 — packet-derived resources and grading contract.
    # Forwarded from coach_open/rex_rechallenge so evaluate_answer and
    # sage_respond operate on the same packet the challenge came from.
    official_docs: list[str]
    skill_builder_links: list[str]
    lab_links: list[str]
    expected_answer_criteria: str
    traps: list[str]
    # Phase 11 — option-based session contract. App-controlled mode; options
    # are exactly 4 labeled A/B/C/D; answer_key is the set of correct labels.
    response_mode: ResponseMode
    options: list[dict[str, str]]  # [{"label": "A", "text": "..."}, ...]
    answer_key: list[OptionLabel]


class EvaluationResult(TypedDict):
    outcome: str  # "correct" | "incorrect"
    reasoning: str
    answer_intent: str
    # Phase 9.6 — internal concept-miss audit fields. Not used by readiness
    # math; persisted on exchanges for the gap tracker / coach report.
    missed_criteria: list[str]
    triggered_traps: list[str]
    # Phase 11 — option verdict payload. Emitted immediately on evaluation so
    # the UI can mark chosen / correct / missed / incorrect options before Sage
    # streams. All fields are required when the challenge is option-based.
    selected_labels: list[OptionLabel]
    correct_labels: list[OptionLabel]
    missed_labels: list[OptionLabel]
    incorrect_labels: list[OptionLabel]


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
    answer_intent: str
    sage_response: str
    citations: list[Citation]
    # Phase 9.5 / 9.6 — internal audit fields; not used by readiness math.
    missed_criteria: list[str]
    triggered_traps: list[str]
    official_docs: list[str]
    skill_builder_links: list[str]
    lab_links: list[str]  


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
    current_concept_id: str
    current_domain: str
    current_topic: str
    current_topic_id: str
    current_task_statement_id: str
    current_task_statement: str
    current_services: list[str]
    current_source_ids: list[str]
    familiarity_level: str
    # Phase 9.4 / 9.5 — packet fields forwarded by coach_open and refreshed
    # by rex_rechallenge. Declared here so the compiled LangGraph runtime
    # preserves them through every node boundary (rex_challenge, evaluate,
    # sage, rechallenge). The full graph filters output keys against the
    # state schema; any key not declared is silently dropped.
    current_concept_facts: list[str]
    current_concept_traps: list[str]
    current_expected_answer_criteria: str
    current_official_docs: list[str]
    current_skill_builder_links: list[str]
    current_lab_links: list[str]
    rex_difficulty: str  # "easy" | "medium" | "hard"
    max_cycles: int
    focus_domain: str
    # "pressure_drills" | "guided_explanations" | "mixed_review" (default)
    learning_style: str
    local_timezone: str
    # Phase 11 — app-controlled response_mode for the next prompt. Rex nodes
    # read this and force the prompt/parser to honor it. The routes layer
    # seeds it on /session/start and /session/next; rex_rechallenge forwards
    # it through cycle increments.
    current_response_mode: ResponseMode

    # 1-indexed cycle counter, advanced by rex_rechallenge.
    cycle: int

    # Per-cycle working state — overwritten each cycle
    current_challenge: Challenge
    user_answer: str
    answer_intent: str
    last_evaluation: EvaluationResult

    # Accumulated per-session — appended by sage_respond after each cycle
    session_history: Annotated[list[Exchange], operator.add]

    # Written by coach_open when a Postgres session row is created (2.4)
    db_session_id: str

    # Runtime API key — set by routes/session.py when invoking graph, propagated
    # into async nodes so get_llm can find it without crossing event-loop boundaries.
    openrouter_api_key: str


def initial_state(
    user_id: str,
    exam_id: str = "dva-c02",
    local_timezone: str = "UTC",
    max_cycles: int = 2,
    learning_style: str = "",
    focus_domain: str = "",
) -> dict[str, Any]:
    """Returns the initial state dict for a new session."""
    return {
        "user_id": user_id,
        "exam_id": exam_id,
        "curriculum_id": "",
        "curriculum": [],
        "current_concept_id": "",
        "current_domain": "",
        "current_topic": "",
        "current_topic_id": "",
        "current_task_statement_id": "",
        "current_task_statement": "",
        "current_services": [],
        "current_source_ids": [],
        "current_concept_facts": [],
        "current_concept_traps": [],
        "current_expected_answer_criteria": "",
        "current_official_docs": [],
        "current_skill_builder_links": [],
        "current_lab_links": [],
        "familiarity_level": "new",
        "rex_difficulty": "medium",
        "max_cycles": max_cycles,
        "focus_domain": focus_domain,
        "learning_style": learning_style,
        "local_timezone": local_timezone,
        "current_response_mode": "single_response",
        "cycle": 0,
        "current_challenge": {},
        "user_answer": "",
        "answer_intent": "attempt",
        "last_evaluation": {},
        "session_history": [],
        "db_session_id": "",
        "openrouter_api_key": "",
    }
