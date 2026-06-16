# coach_open node — opens a session, picks domain + topic, creates DB session row.

from __future__ import annotations

import logging

from curriculum_repository import choose_today_target, get_active_curriculum
from repositories import create_session
from state import AppState

logger = logging.getLogger(__name__)


async def coach_open(state: AppState) -> dict:
    """Initialise session: domain, topic, cycle counter, db_session_id.

    Persists a `sessions` row in Postgres and stashes the returned UUID in
    state so downstream nodes (sage_respond, coach_close) can attach
    exchanges and stamp ended_at to the same session.
    """
    user_id = state["user_id"]
    exam_id = state["exam_id"]
    target = await choose_today_target(user_id=user_id, exam_id=exam_id)
    curriculum = await get_active_curriculum(user_id=user_id, exam_id=exam_id)
    domain = target["domain"]
    topic = target["topic"]
    curriculum_id = target.get("curriculum_id", "")

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
        "rex_difficulty": target.get("difficulty", "medium"),
        "curriculum_id": curriculum_id,
        "curriculum": curriculum["domains"] if curriculum else [],
        "cycle": 1,
        "db_session_id": db_session_id,
    }
