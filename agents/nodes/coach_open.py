# coach_open node — opens a session, picks domain + topic, creates DB session row.
# Phase 2: domain hardcoded to "Deployment" (Phase 1 default).
# Phase 3 will pull curriculum from Postgres and select today's domain.

from __future__ import annotations

from state import AppState


HARDCODED_DOMAIN = "Deployment"
HARDCODED_TOPIC = "CodeDeploy deployment strategies"


def coach_open(state: AppState) -> dict:
    """Initialise session: domain, topic, cycle counter, pending user answers."""
    initial: dict = {
        "current_domain": HARDCODED_DOMAIN,
        "current_topic": HARDCODED_TOPIC,
        "cycle": 1,
    }
    return initial
