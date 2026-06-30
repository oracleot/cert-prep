from __future__ import annotations

import sys
from pathlib import Path

_AGENTS_DIR = Path(__file__).resolve().parent
if str(_AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENTS_DIR))

from routes.history import SESSION_DETAIL_SQL


def test_history_session_query_qualifies_exchange_columns() -> None:
    assert "SELECT e.cycle, e.domain, e.topic, e.challenge, e.user_answer, e.outcome, " in SESSION_DETAIL_SQL
    assert "ORDER BY e.cycle" in SESSION_DETAIL_SQL
    assert "SELECT cycle, domain, topic" not in SESSION_DETAIL_SQL
    assert "ORDER BY cycle" not in SESSION_DETAIL_SQL
