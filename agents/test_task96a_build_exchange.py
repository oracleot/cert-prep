"""Task 9.6a — _build_exchange extracts and propagates miss fields.

AC1: _build_exchange extracts missed_criteria and triggered_traps from evaluation.

All tests compile and run; they fail until 9.6 is implemented.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

from test_task93_shared import _seed_state
from test_task96_shared import FAKE_CONCEPT

_AGENTS_DIR = Path(__file__).resolve().parent
if str(_AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENTS_DIR))


# ---------------------------------------------------------------------------
# Shared state builder
# ---------------------------------------------------------------------------

def _state_with_challenge_and_eval(
    outcome: str,
    missed_criteria: list,
    triggered_traps: list,
    reasoning: str = "Test.",
) -> dict:
    """Build a seeded state with a challenge and evaluation result."""
    state = _seed_state()
    state.update({
        "current_challenge": {
            "concept_id": FAKE_CONCEPT["id"],
            "domain": "Deployment",
            "topic": "CodePipeline Basics",
            "topic_id": FAKE_CONCEPT["id"],
            "task_statement_id": FAKE_CONCEPT["id"],
            "task_statement": FAKE_CONCEPT["task_statement"],
            "services": FAKE_CONCEPT["services"],
            "source_ids": FAKE_CONCEPT["source_ids"],
            "familiarity_level": "new",
            "scenario": "An engineer configures a pipeline.",
            "question": "Which stage is required?",
            "expected_answer_criteria": FAKE_CONCEPT["expected_answer_criteria"],
            "traps": FAKE_CONCEPT["traps"],
            "official_docs": FAKE_CONCEPT["official_docs"],
            "skill_builder_links": FAKE_CONCEPT["skill_builder_links"],
            "lab_links": FAKE_CONCEPT["lab_links"],
        },
        "user_answer": "Source stage.",
        "last_evaluation": {
            "outcome": outcome,
            "reasoning": reasoning,
            "answer_intent": "attempt",
            "missed_criteria": missed_criteria,
            "triggered_traps": triggered_traps,
        },
        "answer_intent": "attempt",
        "cycle": 1,
        "session_history": [],
        "db_session_id": "",
    })
    return state


# ---------------------------------------------------------------------------
# AC1 — _build_exchange extracts miss fields from evaluation
# ---------------------------------------------------------------------------

class TestAC1_BuildExchangeMissFields:
    """_build_exchange must extract and include missed_criteria and triggered_traps."""

    def test_build_exchange_includes_miss_fields(self):
        """_build_exchange must extract missed_criteria and triggered_traps."""
        import nodes.sage_respond as sage_module

        state = _state_with_challenge_and_eval(
            outcome="incorrect",
            missed_criteria=["CodeBuild defaults to no VPC"],
            triggered_traps=[
                "CodeBuild does NOT run inside a VPC by default; "
                "you must explicitly enable VPC mode."
            ],
        )

        exchange = sage_module._build_exchange(
            state,
            sage_text="The VPC point is important — CodeBuild defaults to no VPC.",
            citations=[],
        )

        assert "missed_criteria" in exchange
        assert "triggered_traps" in exchange
        assert isinstance(exchange["missed_criteria"], list)
        assert isinstance(exchange["triggered_traps"], list)

    def test_missed_criteria_and_triggered_traps_are_correct_values(self):
        """Missed criteria/traps from evaluation must flow through to exchange."""
        import nodes.sage_respond as sage_module

        state = _state_with_challenge_and_eval(
            outcome="incorrect",
            missed_criteria=["CodeBuild defaults to no VPC"],
            triggered_traps=[
                "CodeBuild does NOT run inside a VPC by default; "
                "you must explicitly enable VPC mode."
            ],
        )

        exchange = sage_module._build_exchange(
            state,
            sage_text="CodeBuild does not run in a VPC by default.",
            citations=[],
        )

        assert "CodeBuild defaults to no VPC" in exchange["missed_criteria"]
        assert any(
            "VPC" in trap for trap in exchange["triggered_traps"]
        ), f"triggered_traps must contain VPC trap, got {exchange['triggered_traps']!r}"

    def test_correct_answer_has_empty_miss_fields(self):
        """When outcome is 'correct', missed_criteria and triggered_traps are empty."""
        import nodes.sage_respond as sage_module

        state = _state_with_challenge_and_eval(
            outcome="correct",
            missed_criteria=[],
            triggered_traps=[],
            reasoning="Correct.",
        )

        exchange = sage_module._build_exchange(
            state,
            sage_text="Correct — CodePipeline requires a Source stage.",
            citations=[],
        )
        assert exchange["missed_criteria"] == []
        assert exchange["triggered_traps"] == []
