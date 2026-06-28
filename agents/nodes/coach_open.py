# coach_open node — opens a session, selects concept, creates DB session row.

from __future__ import annotations

import logging

from fastapi import HTTPException
from onboarding_repository import get_learning_style
from repositories import create_session
from state import AppState

from concepts.loader import find_concept
from concepts.packet import concept_packet_fields
# Top-level import so test patches on this module name succeed.
from concepts.selector import NoReadyConcept, select_initial_concept  # noqa: F401

logger = logging.getLogger(__name__)


_DIFFICULTY_RANK = {"easy": 0, "medium": 1, "hard": 2}


def _style_adjusted_difficulty(base: str, learning_style: str) -> str:
    """Shift the curriculum-derived difficulty up or down per learning_style.

    pressure_drills     → +1 step (push toward hard)
    guided_explanations → -1 step (push toward easy)
    mixed_review / ""   → unchanged
    """
    rank = _DIFFICULTY_RANK.get(base, 1)
    if learning_style == "pressure_drills":
        rank = min(rank + 1, 2)
    elif learning_style == "guided_explanations":
        rank = max(rank - 1, 0)
    for name, value in _DIFFICULTY_RANK.items():
        if value == rank:
            return name
    return base


async def coach_open(state: AppState) -> dict:
    """Initialise session: select concept, domain, topic, cycle counter, db_session_id.

    Persists a `sessions` row in Postgres and stashes the returned UUID in
    state so downstream nodes (sage_respond, coach_close) can attach
    exchanges and stamp ended_at to the same session.

    Raises HTTPException(422) if no ready concept exists for the requested domain.
    """
    from curriculum_repository import get_active_curriculum

    user_id = state["user_id"]
    exam_id = state["exam_id"]
    focus_domain = state.get("focus_domain") or None

    if state.get("current_concept_id"):
        # Honor the pinned concept set by apply_mode_to_state (mode=review); do NOT re-select.
        concept = find_concept(exam_id, state["current_concept_id"])
    else:
        try:
            concept = select_initial_concept(exam_id, domain=focus_domain)
        except NoReadyConcept as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    domain = concept["domain"]
    concept_id = concept["id"]
    packet = concept_packet_fields(concept)
    topic = packet["topic"]

    curriculum = await get_active_curriculum(user_id=user_id, exam_id=exam_id)
    learning_style = state.get("learning_style") or await get_learning_style(user_id)
    if learning_style not in {"pressure_drills", "guided_explanations", "mixed_review"}:
        learning_style = "mixed_review"

    base_difficulty = packet["difficulty"]
    difficulty = _style_adjusted_difficulty(base_difficulty, learning_style)

    db_session_id = ""
    try:
        db_session_id = await create_session(
            user_id=user_id,
            exam_id=exam_id,
            domain=domain,
            topic=topic,
            curriculum_id=curriculum["id"] if curriculum else "",
            concept_id=concept_id,
        )
    except Exception:
        logger.exception("Failed to create sessions row; continuing without DB persistence.")

    return {
        "current_concept_id": concept_id,
        "current_domain": domain,
        "current_topic": topic,
        "current_topic_id": packet["topic_id"],
        "current_task_statement_id": packet["task_statement_id"],
        "current_task_statement": concept.get("task_statement", ""),
        "current_services": packet["services"],
        "current_source_ids": packet["source_ids"],
        "familiarity_level": packet["familiarity_level"],
        "rex_difficulty": difficulty,
        "curriculum_id": curriculum["id"] if curriculum else "",
        "curriculum": curriculum["domains"] if curriculum else [],
        # Phase 9.4 / 9.5 — surface the curated packet fields so downstream
        # nodes (rex_challenge, evaluate_answer, sage_respond) can ground
        # their prompts to the concept record without re-loading it.
        "current_concept_facts": packet["facts"],
        "current_concept_traps": packet["traps"],
        "current_expected_answer_criteria": packet["expected_answer_criteria"],
        "current_official_docs": packet["official_docs"],
        "current_skill_builder_links": packet["skill_builder_links"],
        "current_lab_links": packet["lab_links"],
        "cycle": 1,
        "db_session_id": db_session_id,
        "learning_style": learning_style,
    }
