"""Task 9.6b — Persisted exchange includes miss fields.

AC2: create_exchange persists missed_criteria and triggered_traps.

All tests compile and run; they fail until 9.6 is implemented.
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from test_task93_shared import _node_graph, _seed_state
from test_task96a_exchange_miss_fields import FAKE_CONCEPT
from test_task95_shared import FakeSageLLM

_AGENTS_DIR = Path(__file__).resolve().parent
if str(_AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENTS_DIR))


# ---------------------------------------------------------------------------
# AC2 — Persisted exchange record includes miss fields
# ---------------------------------------------------------------------------

class TestAC2_PersistedExchangeIncludesMissFields:
    """create_exchange must persist missed_criteria and triggered_traps."""

    def test_create_exchange_signature_has_miss_fields(self):
        """create_exchange must accept missed_criteria and triggered_traps."""
        import inspect
        from repositories import create_exchange

        sig = inspect.signature(create_exchange)
        params = list(sig.parameters.keys())
        assert "missed_criteria" in params
        assert "triggered_traps" in params

    def test_sage_respond_passes_miss_fields_to_create_exchange(self):
        """sage_respond must pass missed_criteria + triggered_traps to create_exchange."""
        from nodes import coach_open as coach_open_module

        concept = dict(FAKE_CONCEPT)
        with patch.object(coach_open_module, "select_initial_concept", return_value=concept):
            state = _seed_state()
            graph = _node_graph()
            state_after_coach = graph.invoke(state, node="coach_open")

            state_after_coach.update({
                "current_challenge": {
                    "concept_id": concept["id"],
                    "domain": "Deployment",
                    "topic": "CodePipeline Basics",
                    "topic_id": concept["id"],
                    "task_statement_id": concept["id"],
                    "task_statement": concept["task_statement"],
                    "services": concept["services"],
                    "source_ids": concept["source_ids"],
                    "familiarity_level": "new",
                    "scenario": "Test.",
                    "question": "What?",
                    "official_docs": concept["official_docs"],
                    "skill_builder_links": [],
                    "lab_links": [],
                },
                "user_answer": "Source stage.",
                "last_evaluation": {
                    "outcome": "incorrect",
                    "reasoning": "Missed the VPC trap.",
                    "answer_intent": "attempt",
                    "missed_criteria": ["CodeBuild defaults to no VPC"],
                    "triggered_traps": [
                        "CodeBuild does NOT run inside a VPC by default; "
                        "you must explicitly enable VPC mode."
                    ],
                },
                "answer_intent": "attempt",
                "cycle": 1,
                "session_history": [],
                "db_session_id": "fake-session-uuid",
            })

        from repositories import create_exchange as real_create_exchange
        calls = []

        async def tracking_create_exchange(**kwargs):
            calls.append(kwargs)

        import nodes.sage_respond as sage_module
        with patch.object(sage_module, "get_llm", return_value=FakeSageLLM(
            "CodeBuild does not run in a VPC by default."
        )):
            with patch.object(sage_module, "create_exchange", side_effect=tracking_create_exchange):
                # Fixed: submit coroutine directly, not double-wrapped.
                import concurrent.futures

                async def _run():
                    return await sage_module.sage_depth(state_after_coach, {})

                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                    future = pool.submit(asyncio.run, _run())
                    future.result()

        assert len(calls) >= 1, "sage_respond must call create_exchange"
        last_call = calls[-1]
        assert "missed_criteria" in last_call
        assert "triggered_traps" in last_call
        assert last_call["missed_criteria"] == ["CodeBuild defaults to no VPC"]
        assert any("VPC" in t for t in last_call["triggered_traps"]), (
            f"triggered_traps must include VPC trap, got {last_call['triggered_traps']!r}"
        )
