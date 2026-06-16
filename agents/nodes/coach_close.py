# coach_close node — wraps up a session, marks it complete.
# Phase 2: returns the final session_history count and a simple outcome tally.
# Phase 4: stamps ended_at and updates domain performance/readiness aggregates.

from __future__ import annotations

import logging

from curriculum_repository import active_domains_for
from performance_repository import persist_readiness_score, record_session_history
from repositories import close_session
from state import AppState
from streak_repository import record_completed_session

logger = logging.getLogger(__name__)


async def coach_close(state: AppState) -> dict:
    """Finalise the session — count outcomes, mark session ended in DB."""
    history = state.get("session_history", [])
    correct = sum(1 for ex in history if ex.get("outcome") == "correct")

    session_id = state.get("db_session_id", "")
    if session_id:
        try:
            await close_session(session_id)
        except Exception:
            logger.exception("Failed to close sessions row; continuing without DB persistence.")

    try:
        domains = state.get("curriculum", []) or await active_domains_for(state["user_id"], state["exam_id"])
        await record_session_history(
            user_id=state["user_id"],
            exam_id=state["exam_id"],
            history=history,
        )
        await persist_readiness_score(
            user_id=state["user_id"],
            exam_id=state["exam_id"],
            domains=domains,
        )
        await record_completed_session(
            state["user_id"],
            state["exam_id"],
            state.get("local_timezone", "UTC"),
        )
    except Exception:
        logger.exception("Failed to update performance/readiness/streak aggregates.")

    return {
        "session_history": [
            {
                "cycle": -1,
                "domain": "__summary__",
                "topic": "__summary__",
                "challenge": {},
                "user_answer": "",
                "outcome": "summary",
                "sage_response": f"Session complete: {correct}/{len(history)} correct",
                "citations": [],
            }
        ],
    }
