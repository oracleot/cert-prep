"""Shared helpers for task 9.3 closed-book concept tests."""
from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path

import pytest

_AGENTS_DIR = Path(__file__).resolve().parent
if str(_AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENTS_DIR))

from state import initial_state


# ---------------------------------------------------------------------------
# Mock LLM
# ---------------------------------------------------------------------------

class FakeLLMResponse:
    def __init__(self, content: str = '') -> None:
        self.content = content


class FakeLLM:
    """Minimal mock matching the ChatOpenAI interface used by session graph nodes."""

    def __init__(self, response_content: str = '') -> None:
        self._content = response_content

    def invoke(self, *a, **k):
        return FakeLLMResponse(self._content)

    async def ainvoke(self, *a, **k):
        return FakeLLMResponse(self._content)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _seed_state(**kwargs) -> dict:
    base = initial_state(
        user_id=kwargs.get("user_id", f"test-{uuid.uuid4().hex[:8]}"),
        exam_id="dva-c02",
        max_cycles=2,
    )
    base.update(kwargs)
    return base


def _node_graph():
    """Graph via get_session_graph() with InMemorySaver (no Postgres required)."""
    import asyncio as _asyncio
    import graphs.session as _gs

    os.environ.pop("DATABASE_URL", None)
    _gs._cached_graph = None

    import db as _db
    _asyncio.run(_db.init_checkpointer())

    from graphs.session import get_session_graph
    return get_session_graph()
