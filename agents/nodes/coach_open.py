# coach_open node — opens a session, picks domain + topic, creates DB session row.

from __future__ import annotations

import logging

from curriculum_repository import choose_today_target, get_active_curriculum
from onboarding_repository import get_learning_style
from repositories import create_session
from state import AppState

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
    """Initialise session: domain, topic, cycle counter, db_session_id.

    Persists a `sessions` row in Postgres and stashes the returned UUID in
    state so downstream nodes (sage_respond, coach_close) can attach
    exchanges and stamp ended_at to the same session.
    """
    user_id = state["user_id"]
    exam_id = state["exam_id"]
    target = await choose_today_target(user_id=user_id, exam_id=exam_id, focus_domain=state.get("focus_domain", ""))
    curriculum = await get_active_curriculum(user_id=user_id, exam_id=exam_id)
    learning_style = state.get("learning_style") or await get_learning_style(user_id)
    if learning_style not in {"pressure_drills", "guided_explanations", "mixed_review"}:
        learning_style = "mixed_review"
    domain = target["domain"]
    topic = target["topic"]
    curriculum_id = target.get("curriculum_id", "")

    base_difficulty = target.get("difficulty", "medium")
    difficulty = _style_adjusted_difficulty(base_difficulty, learning_style)

    db_session_id = ""
    try:
        db_session_id = await create_session(
            user_id=user_id,
            exam_id=exam_id,
            domain=domain,
            topic=topic,
            curriculum_id=curriculum_id,
        )
    except Exception:
        logger.exception("Failed to create sessions row; continuing without DB persistence.")

    return {
        "current_domain": domain,
        "current_topic": topic,
        "current_topic_id": target.get("topic_id", ""),
        "current_task_statement_id": target.get("task_statement_id", ""),
        "current_task_statement": target.get("task_statement", ""),
        "current_services": target.get("services", []),
        "current_source_ids": target.get("source_ids", []),
        "familiarity_level": target.get("familiarity_level", "new"),
        "rex_difficulty": difficulty,
        "curriculum_id": curriculum_id,
        "curriculum": curriculum["domains"] if curriculum else [],
        "cycle": 1,
        "db_session_id": db_session_id,
        "learning_style": learning_style,
    }
