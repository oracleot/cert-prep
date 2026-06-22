# coach_close node — wraps up a session, marks it complete.
# Phase 2: returns the final session_history count and a simple outcome tally.
# Phase 4: stamps ended_at and updates domain performance/readiness aggregates.

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from typing import Any

from curriculum_repository import active_domains_for
from db import get_pool, has_pool
from domain_difficulty_repository import record_domain_difficulty_sessions
from performance_repository import persist_readiness_score, record_session_history
from repositories import close_session
from state import AppState
from streak_repository import record_completed_session

logger = logging.getLogger(__name__)


async def _active_history(session_id: str, history: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    if not session_id or not has_pool():
        return list(history)
    pool = get_pool()
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT cycle FROM exchanges WHERE session_id = %s AND review_status != 'active'",
                (session_id,),
            )
            excluded_cycles = {row[0] for row in await cur.fetchall()}
    return [item for item in history if item.get("cycle") not in excluded_cycles]


async def coach_close(state: AppState) -> dict:
    """Finalise the session — count outcomes, mark session ended in DB."""
    history = state.get("session_history", [])
    session_id = state.get("db_session_id", "")
    active_history = await _active_history(session_id, history)
    correct = sum(1 for ex in active_history if ex.get("outcome") == "correct")

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
            history=active_history,
        )
        await record_domain_difficulty_sessions(
            user_id=state["user_id"],
            exam_id=state["exam_id"],
            history=active_history,
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
                "answer_intent": "attempt",
                "sage_response": f"Session complete: {correct}/{len(active_history)} correct",
                "citations": [],
            }
        ],
    }
