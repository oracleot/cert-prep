"""Task 9.5c — Exchange persists concept link metadata.

AC3: Stored exchanges include official_docs/skill_builder_links/lab_links
     for audit.

All tests compile and run; they fail until 9.5 is implemented.
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from test_task93_shared import _node_graph, _seed_state
from test_task95_shared import FAKE_CONCEPT, FakeSageLLM, run_sage_depth_sync

_AGENTS_DIR = Path(__file__).resolve().parent
if str(_AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENTS_DIR))


# ---------------------------------------------------------------------------
# AC3 — Stored exchanges include concept link metadata
# ---------------------------------------------------------------------------

class TestAC3_ExchangePersistsLinkMetadata:
    """create_exchange must persist concept links for audit."""

    def test_create_exchange_accepts_official_docs_and_skill_builder_links(self):
        """create_exchange must accept official_docs, skill_builder_links, lab_links."""
        import inspect
        from repositories import create_exchange

        sig = inspect.signature(create_exchange)
        param_names = list(sig.parameters.keys())
        assert "official_docs" in param_names
        assert "skill_builder_links" in param_names
        assert "lab_links" in param_names

    def test_sage_respond_passes_concept_links_to_create_exchange(self):
        """sage_respond must extract and pass official_docs/skill_builder_links/lab_links
        to create_exchange when persisting an exchange."""
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
                    "skill_builder_links": concept["skill_builder_links"],
                    "lab_links": concept["lab_links"],
                },
                "user_answer": "Source stage.",
                "last_evaluation": {
                    "outcome": "correct",
                    "reasoning": "Correct.",
                    "answer_intent": "attempt",
                    "missed_criteria": [],
                    "triggered_traps": [],
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
        fake_response = (
            "CodePipeline requires a Source stage. "
            "See https://docs.aws.amazon.com/codepipeline/latest/userguide/"
        )
        with patch.object(sage_module, "get_llm", return_value=FakeSageLLM(fake_response)):
            with patch.object(sage_module, "create_exchange", side_effect=tracking_create_exchange):
                # Fixed: pass coroutine directly to pool.submit, not double-wrapped.
                import concurrent.futures

                async def _run():
                    return await sage_module.sage_depth(state_after_coach, {})

                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                    future = pool.submit(asyncio.run, _run())
                    future.result()

        assert len(calls) >= 1, "sage_respond must call create_exchange"
        last_call = calls[-1]
        assert "official_docs" in last_call
        assert "skill_builder_links" in last_call
        assert "lab_links" in last_call
