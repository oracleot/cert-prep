# coach_close node — wraps up a session, marks it complete.
# Phase 2: returns the final session_history count and a simple outcome tally.
# Phase 3: stamps ended_at and updates domain performance aggregates.

from __future__ import annotations

import logging

from performance_repository import record_session_history
from repositories import close_session
from state import AppState

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
        await record_session_history(
            user_id=state["user_id"],
            exam_id=state.get("exam_id", "dva-c02"),
            history=history,
        )
    except Exception:
        logger.exception("Failed to update performance aggregates.")

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
