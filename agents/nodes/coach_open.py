# coach_open node — opens a session, picks domain + topic, creates DB session row.
# Phase 2: domain hardcoded to "Deployment" (Phase 1 default).
# Phase 3 will pull curriculum from Postgres and select today's domain.

from __future__ import annotations

import logging

from repositories import create_session
from state import AppState

logger = logging.getLogger(__name__)


HARDCODED_DOMAIN = "Deployment"
HARDCODED_TOPIC = "CodeDeploy deployment strategies"


async def coach_open(state: AppState) -> dict:
    """Initialise session: domain, topic, cycle counter, db_session_id.

    Persists a `sessions` row in Postgres and stashes the returned UUID in
    state so downstream nodes (sage_respond, coach_close) can attach
    exchanges and stamp ended_at to the same session.
    """
    domain = HARDCODED_DOMAIN
    user_id = state.get("user_id", "dev-user")
    exam_id = state.get("exam_id", "dva-c02")

    db_session_id = ""
    try:
        db_session_id = await create_session(user_id=user_id, exam_id=exam_id, domain=domain)
    except Exception:
        logger.exception("Failed to create sessions row; continuing without DB persistence.")

    return {
        "current_domain": domain,
        "current_topic": HARDCODED_TOPIC,
        "cycle": 1,
        "db_session_id": db_session_id,
    }
