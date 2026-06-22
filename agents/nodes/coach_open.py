# coach_open node — opens a session, selects concept, creates DB session row.

from __future__ import annotations

import logging

from fastapi import HTTPException
from onboarding_repository import get_learning_style
from repositories import create_session
from state import AppState

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

    try:
        concept = select_initial_concept(exam_id, domain=focus_domain)
    except NoReadyConcept as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    domain = concept["domain"]
    # topic is the short human-readable label; concept_id is the stable key.
    topic = concept.get("topic", concept["id"])
    concept_id = concept["id"]

    curriculum = await get_active_curriculum(user_id=user_id, exam_id=exam_id)
    learning_style = state.get("learning_style") or await get_learning_style(user_id)
    if learning_style not in {"pressure_drills", "guided_explanations", "mixed_review"}:
        learning_style = "mixed_review"

    base_difficulty = concept.get("difficulty", "medium") if concept.get("difficulty") else "medium"
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
        "current_topic_id": concept.get("topic_id", concept_id),
        "current_task_statement_id": concept.get("task_statement_id", concept_id),
        "current_task_statement": concept.get("task_statement", ""),
        "current_services": concept.get("services", []),
        "current_source_ids": concept.get("source_ids", []),
        "familiarity_level": concept.get("familiarity_level", "new"),
        "rex_difficulty": difficulty,
        "curriculum_id": curriculum["id"] if curriculum else "",
        "curriculum": curriculum["domains"] if curriculum else [],
        "cycle": 1,
        "db_session_id": db_session_id,
        "learning_style": learning_style,
    }
