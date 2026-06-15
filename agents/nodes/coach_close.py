# coach_close node — wraps up a session, marks it complete.
# Phase 2: returns the final session_history count and a simple outcome tally.
# Phase 4 will persist aggregates to Postgres (readiness score, rex record).

from __future__ import annotations

from state import AppState


def coach_close(state: AppState) -> dict:
    """Finalise the session — count outcomes, no-op persistence in 2.3."""
    history = state.get("session_history", [])
    correct = sum(1 for ex in history if ex.get("outcome") == "correct")

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
            }
        ],
    }
